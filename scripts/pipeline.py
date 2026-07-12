#!/usr/bin/env python3
"""
Harness Pipeline — plan → plan-review → implement → pre-commit → make-pr → compound 를
한 phase 씩 돌리고, phase.json 으로 어느 stage 까지 왔는지 추적한다.

기본은 대화형: init 으로 phase 를 만들고, status 로 "지금 실행할 스킬"을 확인해
그 스킬을 세션에서 직접 실행한 뒤 advance 로 다음 stage 로 넘어간다.
--headless(run)는 각 stage 를 claude -p 로 자동 실행한다. (docs/solutions/pipeline.md 참고)

Usage:
    python3 scripts/pipeline.py init <phase-name>
    python3 scripts/pipeline.py status [phase]
    python3 scripts/pipeline.py advance [phase] [--summary "..."]
    python3 scripts/pipeline.py run [phase]      # headless: 남은 stage 자동 실행
    python3 scripts/pipeline.py selftest
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHASES = ROOT / "phases"
KST = timezone(timedelta(hours=9))

# stage 이름 → 실행할 action. "/"로 시작하면 스킬(대화형/claude -p), 아니면 셸 명령.
# implement 는 OMC /ultrawork(선작업 0). step 단위까지 자동화하려면 "execute.py <slug>" 로 교체.
# lefthook 이 commit 시 lint 를 돌리므로 commit-push stage 가 곧 "pre-commit" 역할.
STAGES = [
    ("plan", "/plan"),
    ("plan-review-ceo", "/plan-ceo-review"),
    ("plan-review-eng", "/plan-eng-review"),
    ("implement", "/ultrawork"),
    ("commit-push", "git add -A && git commit && git push -u origin HEAD"),
    ("make-pr", "/make-pr"),
    ("compound", "/ce-compound"),
]

# init 때 한 번 물어보고 생략할 수 있는 선택 stage.
REVIEW_STAGES = {"plan-review-ceo", "plan-review-eng"}


def _stamp() -> str:
    return datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S%z")


def _read(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _write(p: Path, data: dict):
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _slug(name: str) -> str:
    s = re.sub(r"[^0-9a-zA-Z가-힣-]+", "-", name.strip().lower())
    return re.sub(r"-+", "-", s).strip("-")


def _run_git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(ROOT), capture_output=True, text=True)


# --- 순수 상태 로직 (git/io 없음 → selftest 대상) --------------------------

def new_phase_doc(slug: str, include_review: bool = True) -> dict:
    stages = [(n, a) for n, a in STAGES if include_review or n not in REVIEW_STAGES]
    return {
        "phase": slug,
        "branch": f"feat-{slug}",
        "created_at": _stamp(),
        "cursor": 0,
        "stages": [{"name": n, "action": a, "status": "pending"} for n, a in stages],
    }


def mark_advance(doc: dict, summary: str | None = None) -> dict:
    i = doc["cursor"]
    if i >= len(doc["stages"]):
        return doc
    stage = doc["stages"][i]
    stage["status"] = "completed"
    stage["completed_at"] = _stamp()
    if summary:
        stage["summary"] = summary
    doc["cursor"] = i + 1
    if doc["cursor"] >= len(doc["stages"]):
        doc["completed_at"] = _stamp()
    return doc


# --- 경로/조회 -------------------------------------------------------------

def _phase_file(slug: str) -> Path:
    return PHASES / slug / "phase.json"


def _resolve(arg: str | None) -> Path:
    """인자로 받은 phase, 없으면 진행 중(cursor<총) phase 하나를 찾는다."""
    if arg:
        f = _phase_file(_slug(arg))
        if not f.exists():
            sys.exit(f"ERROR: {f} 없음. 먼저 init 하세요.")
        return f
    active = [
        f for f in PHASES.glob("*/phase.json")
        if _read(f)["cursor"] < len(_read(f)["stages"])
    ]
    if not active:
        sys.exit("진행 중인 phase 가 없어요. `pipeline.py init <name>` 으로 시작하세요.")
    if len(active) > 1:
        names = ", ".join(f.parent.name for f in active)
        sys.exit(f"진행 중 phase 가 여러 개예요 ({names}). 인자로 하나 지정하세요.")
    return active[0]


def _show_next(doc: dict):
    i = doc["cursor"]
    if i >= len(doc["stages"]):
        print(f"  ✓ '{doc['phase']}' 모든 stage 완료. 새 phase 는 `init`.")
        return
    s = doc["stages"][i]
    kind = "스킬" if s["action"].startswith("/") else "명령"
    print(f"  ▶ [{i + 1}/{len(doc['stages'])}] {s['name']} — {kind}: {s['action']}")
    if s["action"].startswith("/"):
        print(f"    대화형: 이 스킬을 실행 후 `pipeline.py advance` 로 넘어가세요.")
    elif s["name"] == "commit-push":
        # 메시지는 임의가 아니라 Conventional Commits 규칙. git-master 위임이 제일 편함.
        print(f"    메시지 규칙: feat({doc['phase']}): <뭐 했는지>  (git-master/ce-commit 위임 권장)")
        print(f"    실행 후 `pipeline.py advance`.")
    else:
        print(f"    실행: {s['action']}  → 통과하면 `pipeline.py advance`.")


# --- 서브커맨드 ------------------------------------------------------------

def _ask_review(no_review: bool) -> bool:
    """plan-review stage 를 포함할지 한 번만 물어본다.
    --no-review 면 안 물어보고 생략. 비대화형(headless)이면 기본 포함."""
    if no_review:
        return False
    if not sys.stdin.isatty():
        return True
    ans = input("  plan review(CEO/Eng) stage 를 실행할까요? [Y/n] ").strip().lower()
    return ans not in ("n", "no")


def cmd_init(name: str, no_review: bool = False):
    """phase 전용 worktree(.claude/worktrees/<slug>)를 만들고 그 안에 phase.json 을 심는다.
    메인 체크아웃 브랜치는 건드리지 않아 phase 를 병렬로 돌릴 수 있다."""
    slug = _slug(name)
    branch = f"feat-{slug}"
    wt = ROOT / ".claude" / "worktrees" / slug
    f = wt / "phases" / slug / "phase.json"
    if f.exists():
        sys.exit(f"ERROR: {f} 이미 있음.")
    include_review = _ask_review(no_review)
    if not wt.exists():
        exists = _run_git("rev-parse", "--verify", branch).returncode == 0
        r = _run_git("worktree", "add", str(wt), *([branch] if exists else ["-b", branch]))
        if r.returncode != 0:
            sys.exit(f"ERROR: worktree '{wt}' 생성 실패: {r.stderr.strip()}")
    f.parent.mkdir(parents=True, exist_ok=True)
    _write(f, new_phase_doc(slug, include_review))
    if not include_review:
        print("  (plan review 생략)")
    print(f"  Phase '{slug}' 시작 (worktree: {wt}, branch: {branch})")
    print(f"  이후 명령은 worktree 안에서 실행하세요: cd {wt}")
    _show_next(_read(f))


def cmd_status(arg):
    _show_next(_read(_resolve(arg)))


def cmd_advance(arg, summary):
    f = _resolve(arg)
    doc = mark_advance(_read(f), summary)
    _write(f, doc)
    _show_next(doc)


def cmd_run(arg):
    """headless: 남은 stage 를 claude -p / 셸로 자동 실행. 실패하면 그 자리에서 멈춘다."""
    f = _resolve(arg)
    doc = _read(f)
    while doc["cursor"] < len(doc["stages"]):
        s = doc["stages"][doc["cursor"]]
        name, action = s["name"], s["action"]
        if not action.startswith("/"):
            # 명령 stage(commit-push 등)는 메시지·판단이 필요해 headless 자동화 대상이 아님.
            sys.exit(f"  ⏸ '{name}' 은 명령 stage 예요. 직접 실행 후 advance:\n    {action}")
        print(f"  ▶ {name}: {action}")
        prompt = f"{action} — phase '{doc['phase']}' 작업."
        r = subprocess.run(
            ["claude", "-p", "--dangerously-skip-permissions", prompt],
            cwd=str(ROOT), capture_output=True, text=True, timeout=1800,
        )
        (f.parent / f"stage-{name}-output.json").write_text(
            json.dumps({"stage": name, "exitCode": r.returncode,
                        "stdout": r.stdout, "stderr": r.stderr},
                       indent=2, ensure_ascii=False), encoding="utf-8")
        if r.returncode != 0:
            sys.exit(f"  ✗ '{name}' 실패 (code {r.returncode}). 고친 뒤 다시 run.")
        doc = mark_advance(doc)
        _write(f, doc)
        print(f"  ✓ {name}")
    print(f"  ✓ '{doc['phase']}' 완료.")


def selftest():
    doc = new_phase_doc("데모-phase")
    assert doc["branch"] == "feat-데모-phase"
    assert doc["cursor"] == 0 and len(doc["stages"]) == len(STAGES)
    for i in range(len(STAGES)):
        assert doc["cursor"] == i
        mark_advance(doc, summary=f"s{i}")
    assert doc["cursor"] == len(STAGES)
    assert "completed_at" in doc
    assert all(s["status"] == "completed" for s in doc["stages"])
    mark_advance(doc)  # 끝난 뒤 advance 는 no-op
    assert doc["cursor"] == len(STAGES)
    no_rev = new_phase_doc("데모", include_review=False)
    assert len(no_rev["stages"]) == len(STAGES) - len(REVIEW_STAGES)
    assert not any(s["name"] in REVIEW_STAGES for s in no_rev["stages"])
    assert _slug("Share Fortune!!") == "share-fortune"
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description="Harness Pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("name")
    p.add_argument("--no-review", action="store_true", help="plan-review(ceo/eng) stage 생략(안 물어봄)")
    p = sub.add_parser("status"); p.add_argument("phase", nargs="?")
    p = sub.add_parser("advance"); p.add_argument("phase", nargs="?"); p.add_argument("--summary")
    p = sub.add_parser("run"); p.add_argument("phase", nargs="?")
    sub.add_parser("selftest")
    a = ap.parse_args()

    if a.cmd == "init":
        cmd_init(a.name, a.no_review)
    elif a.cmd == "status":
        cmd_status(a.phase)
    elif a.cmd == "advance":
        cmd_advance(a.phase, a.summary)
    elif a.cmd == "run":
        cmd_run(a.phase)
    elif a.cmd == "selftest":
        selftest()


if __name__ == "__main__":
    main()
