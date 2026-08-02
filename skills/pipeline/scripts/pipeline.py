#!/usr/bin/env python3
"""
Harness Pipeline — discuss → plan → plan-review → approve → implement(red/green) →
verify → commit-push → make-pr → compound 를 한 phase 씩 돌리고,
phase.json 으로 어느 stage 까지 왔는지 추적한다.

기본은 대화형: init 으로 phase 를 만들고, status 로 "지금 실행할 스킬"을 확인해
그 스킬을 세션에서 직접 실행한 뒤 advance 로 다음 stage 로 넘어간다.
--headless(run)는 각 stage 를 claude -p 로 자동 실행한다. (docs/solutions/pipeline.md 참고)

Usage:
    python3 pipeline.py init <phase-name>
    python3 pipeline.py status [phase]
    python3 pipeline.py advance [phase] [--summary "..."]
    python3 pipeline.py run [phase]      # headless: 남은 stage 자동 실행
    python3 pipeline.py done <phase>     # worktree 제거 + 브랜치 정리 (compound 미수행이면 거부)
    python3 pipeline.py selftest
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


def _git_root() -> Path:
    """ROOT 는 스크립트 위치가 아니라 cwd 기준 git root. plugin 설치 시 스크립트는
    ~/.claude/plugins/ 캐시에 있으므로, phase 는 '지금 작업 중인 레포'에 속해야 한다.
    worktree 안에서 실행하면 worktree root 가 잡혀 기존 동작이 유지된다.

    git 밖이면 죽는다(fail-closed). cwd 로 폴백하면 에이전트가 다른 디렉토리에 있거나
    서브에이전트 cwd 가 다를 때 조용히 엉뚱한 곳에 phases/ 를 만든다.
    모듈 로드 시점에 평가되므로 selftest·--help 도 git repo 안에서만 돈다 — 의도된 비용."""
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ERROR: git repo 밖에서 실행됐어요 — phase 위치를 결정할 수 없어요.\n"
                 "  대상 레포 안에서 실행하세요.")
    return Path(r.stdout.strip())


ROOT = _git_root()
PHASES = ROOT / "phases"
KST = timezone(timedelta(hours=9))

# stage 이름 → 실행할 action. "/"로 시작하면 스킬(대화형/claude -p), 아니면 셸 명령.
# discuss/approve 는 INTERACTIVE_STAGES — 스킬도 명령도 아닌 대화형 stage.
# implement/verify 는 OMC(/ultrawork·/verify) 하드 의존 (ADR-004).
# 스킬 stage 를 추가/변경하면 pipeline SKILL.md §0-1 의 사전 점검 표도 함께 갱신한다.
STAGES = [
    ("discuss", "이슈·요구사항을 사용자와 자유 대화로 논의"),
    ("plan", "/plan"),
    ("plan-review-ceo", "/plan-ceo-review"),
    ("plan-review-eng", "/plan-eng-review"),
    ("approve", "phases/<slug>/plan.md 를 사용자에게 승인받기"),
    ("implement", "/ultrawork"),
    ("verify", "/verify"),
    ("commit-push", "커밋 범위 확인 후 git commit && git push -u origin HEAD"),
    ("make-pr", "/make-pr"),
    ("compound", "/ce-compound"),
]

# init 때 한 번 물어보고 생략할 수 있는 선택 stage.
REVIEW_STAGES = {"plan-review-ceo", "plan-review-eng"}
COMPOUND_STAGE = "compound"  # 교훈 기록(CLAUDE.md 5장). /ce-compound 로 수동 실행이라 생략 가능.
INTERACTIVE_STAGES = {"discuss", "approve"}  # 사람과의 대화가 곧 실행 — headless 불가.

# TDD 시 implement 자리에 splice 되는 record 쌍. hint 는 red/green 전용 optional 필드라
# 접근은 항상 s.get("hint", ""). 문구의 원본은 SKILL.md §2 — 수정 시 함께 갱신.
TDD_PAIR = [
    {"name": "implement-red", "action": "/ultrawork",
     "hint": "RED: 실패하는 테스트만 먼저 작성하고, 올바른 이유로 실패하는지 확인. 구현 코드는 건드리지 않기."},
    {"name": "implement-green", "action": "/ultrawork",
     "hint": "GREEN: 최소 구현으로 테스트 통과. red 에서 만든 테스트를 수정해 통과시키는 것 금지."},
]


def _stamp() -> str:
    return datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S%z")


def _read(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _write(p: Path, data: dict):
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _slug(name: str) -> str:
    s = re.sub(r"[^0-9a-zA-Z가-힣-]+", "-", name.strip().lower())
    return re.sub(r"-+", "-", s).strip("-")


def _branch(slug: str) -> str:
    """브랜치는 입력한 이름(slug) 그대로, 항상 대문자."""
    return slug.upper()


def _run_git(*args, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=str(cwd or ROOT), capture_output=True, text=True)


def _main_root() -> Path:
    """메인 체크아웃 루트. worktree 안에서도 `.git` 은 메인 쪽을 가리키므로
    done 은 여기서 git 을 실행해야 자기 worktree 를 제거할 수 있다.
    git 이 cwd 기준 상대 경로(`../.git`)를 줄 수 있어 resolve() 가 필요하다."""
    r = subprocess.run(["git", "rev-parse", "--git-common-dir"],
                       capture_output=True, text=True)
    return Path(r.stdout.strip()).resolve().parent if r.returncode == 0 else ROOT


def _base_branch(main: Path) -> str:
    """PR 의 base. origin/HEAD 가 가리키는 기본 브랜치이고, 없으면 main 으로 본다."""
    r = _run_git("symbolic-ref", "--short", "refs/remotes/origin/HEAD", cwd=main)
    return r.stdout.strip().rsplit("/", 1)[-1] if r.returncode == 0 else "main"


def _branch_changed_files(main: Path, base: str, branch: str) -> list[str] | None:
    """base 대비 이 브랜치가 바꾼 파일. three-dot 이라 base 가 전진해도 남의 커밋이 안 섞인다
    (GUARDRAILS). base 를 못 찾으면 None — 판정 불가와 '안 바꿈'을 구별해야 한다."""
    r = _run_git("diff", "--name-only", f"origin/{base}...{branch}", cwd=main)
    return r.stdout.splitlines() if r.returncode == 0 else None


def _pr_status(main: Path, branch: str) -> tuple[str, list[str]] | None:
    """이 브랜치 PR 의 (state, PR 에 포함된 커밋 SHA 목록). 판정 불가면 None.

    로컬 git 은 squash 머지를 판정하지 못한다 — `branch -d`·`log A..B`·`cherry` 는 전부
    "미머지"라고 답한다. GitHub 은 확정적으로 알고, 머지 뒤에 붙은 커밋도 PR 목록에 없어서
    드러난다(issue #32 의 사고가 정확히 그 모양이었다).

    None 을 주는 경우가 여럿이라 호출부는 내용 비교로 폴백한다: gh 미설치·미인증,
    비-GitHub 레포, 오프라인, 그 브랜치의 PR 없음."""
    try:
        r = subprocess.run(
            ["gh", "pr", "list", "--head", branch, "--state", "all", "--limit", "1",
             "--json", "state,commits"],
            cwd=str(main), capture_output=True, text=True)
    except OSError:
        return None  # gh 미설치
    if r.returncode != 0:
        return None  # 미인증·비-GitHub·네트워크
    try:
        prs = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None
    if not prs:
        return None  # PR 없음
    return prs[0].get("state", ""), [c["oid"] for c in prs[0].get("commits", [])]


def _arrived(main: Path, base: str, branch: str, path: str) -> bool:
    """이 파일의 내용이 origin/<base> 에 도착했는가. two-dot 이라 내용 비교이고,
    squash/rebase/cherry-pick/별도 PR 어느 방식으로 머지돼도 같은 답이 나온다.
    exit 128(잘못된 ref) 도 미도착으로 묶인다 — 판정 불가일 때는 막는 쪽이 안전하다."""
    return _run_git("diff", "--quiet", f"origin/{base}", branch, "--", path,
                    cwd=main).returncode == 0


def _wt_path(root: Path, slug: str) -> Path:
    """phase 전용 worktree 경로. init 과 done 이 갈라지지 않게 한 군데서만 만든다."""
    return root / ".claude" / "worktrees" / slug


# --- 순수 상태 로직 (git/io 없음 → selftest 대상) --------------------------

def new_phase_doc(slug: str, include_review: bool = True, include_compound: bool = True,
                  include_tdd: bool = True) -> dict:
    def keep(name: str) -> bool:
        if not include_review and name in REVIEW_STAGES:
            return False
        if not include_compound and name == COMPOUND_STAGE:
            return False
        return True
    stages = []
    for n, a in STAGES:
        if not keep(n):
            continue
        if n == "implement" and include_tdd:
            # TDD: implement 자리에 red/green 을 splice — 항상 정확히 한 구현 경로만 남는다.
            stages.extend({**s, "status": "pending"} for s in TDD_PAIR)
        else:
            stages.append({"name": n, "action": a, "status": "pending"})
    return {
        "phase": slug,
        "branch": _branch(slug),
        "created_at": _stamp(),
        "cursor": 0,
        "stages": stages,
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


def _blocking(status_lines: list[str]) -> list[str]:
    """`git status --porcelain` 줄에서 '정리해도 되는 것'이 아닌 경로만 골라낸다.
    phases/ 는 done 이 지워도 되는 자기 산출물(CLAUDE.md §6), 나머지는 사용자 작업이다.
    비어 있지 않으면 done 은 아무것도 지우지 않고 멈춘다 — 순서를 뒤집으면
    remove 실패 시 phase 상태만 날아가고 worktree 는 남는다."""
    paths = [ln[3:] for ln in status_lines if ln.strip()]
    return [p for p in paths if not p.startswith("phases/")]


def _solution_notes(changed: list[str], docs_path: str) -> list[str]:
    """이 브랜치가 건드린 <docs>/solutions/ 파일 = compound 로 남긴 것들.
    파이프라인에 compound stage 가 없으므로(ADR-001) done 이 유일한 확인 지점이다.
    bool 이 아니라 목록인 것은 도착 확인(cmd_done)이 이 목록 위에서 돌기 때문 —
    경로 필터를 여기 한 곳에만 두려고 git 쪽엔 pathspec 을 주지 않는다."""
    prefix = f"{docs_path.strip('/')}/solutions/"
    return [p for p in changed if p.startswith(prefix)]


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
    if s["name"] in INTERACTIVE_STAGES:
        kind = "대화형"
    else:
        kind = "스킬" if s["action"].startswith("/") else "명령"
    print(f"  ▶ [{i + 1}/{len(doc['stages'])}] {s['name']} — {kind}: {s['action']}")
    if s.get("hint", ""):
        print(f"    {s['hint']}")
    if s["name"] in INTERACTIVE_STAGES:
        print(f"    대화형: 이 세션에서 사용자와 진행 후 `pipeline.py advance` 로 넘어가세요.")
    elif s["action"].startswith("/"):
        print(f"    대화형: 이 스킬을 실행 후 `pipeline.py advance` 로 넘어가세요.")
    elif s["name"] == "commit-push":
        # 변경분을 통째로 커밋하지 않는다 — 범위를 먼저 확인받는다 (issue #9).
        print(f"    먼저 `git status --short` / `git diff --stat` 요약과 제안 메시지를 보여주고 확인받기:")
        print(f"      이대로 전체 커밋 / 일부만 커밋 / 직전 커밋에 합치기(amend) / 건너뛰기")
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


def cmd_init(name: str, no_review: bool = False, no_worktree: bool = False,
             no_compound: bool = False, no_tdd: bool = False):
    """phase 전용 worktree(.claude/worktrees/<slug>)를 만들고 그 안에 phase.json 을 심는다.
    메인 체크아웃 브랜치는 건드리지 않아 phase 를 병렬로 돌릴 수 있다.
    --no-worktree 면 현재 체크아웃에서 바로 진행한다."""
    slug = _slug(name)
    branch = _branch(slug)
    # 기준은 ROOT 가 아니라 메인 체크아웃 — worktree 안에서 init 해도 중첩되지 않고,
    # done 이 찾는 곳과 항상 같아진다. 메인에서 실행하면 둘은 같은 경로다.
    wt = None if no_worktree else _wt_path(_main_root(), slug)
    f = _phase_file(slug) if wt is None else wt / "phases" / slug / "phase.json"
    if f.exists():
        sys.exit(f"ERROR: {f} 이미 있음.")
    include_review = _ask_review(no_review)
    if wt is not None and not wt.exists():
        exists = _run_git("rev-parse", "--verify", branch).returncode == 0
        r = _run_git("worktree", "add", str(wt), *([branch] if exists else ["-b", branch]))
        if r.returncode != 0:
            sys.exit(f"ERROR: worktree '{wt}' 생성 실패: {r.stderr.strip()}")
    f.parent.mkdir(parents=True, exist_ok=True)
    _write(f, new_phase_doc(slug, include_review, not no_compound, not no_tdd))
    if not include_review:
        print("  (plan review 생략)")
    if no_compound:
        print("  (compound stage 생략 — /ce-compound 는 수동)")
    if no_tdd:
        print("  (TDD 생략 — implement 단일 stage)")
    if wt is None:
        print(f"  Phase '{slug}' 시작 (현재 체크아웃, branch 유지)")
    else:
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


def cmd_done(name: str, force: bool = False):
    """phase 를 끝낸 뒤 worktree 를 제거하고 브랜치를 정리한다.
    완료된 phase 는 _resolve 가 못 찾으므로(cursor == 총 stage 수) 이름을 반드시 받고,
    phase.json 은 worktree 안에 있어 메인에서 안 보이므로 slug 만으로 경로를 유도한다."""
    slug = _slug(name)
    branch = _branch(slug)
    main = _main_root()
    wt = _wt_path(main, slug)
    base = _base_branch(main)  # 게이트와 마지막 안내가 모두 쓴다 (--force 여도 필요)

    # compound 게이트 — 지우기 전에, 아무것도 지우기 전에 확인한다.
    # 묻는 것은 "건드렸는가"가 아니라 "교훈이 origin/<base> 에 도착했는가"다 (issue #32).
    if not force:
        # 로컬 origin/<base> 가 낡으면 도착한 노트를 미도착으로 오판한다. 실패는 무시 —
        # 오프라인이면 있는 ref 로 판정하고, 막는 쪽으로 틀리므로 안전하다.
        # 타임아웃은 걸지 않는다: macOS 기본에 timeout(1) 이 없어 portable 하지 않다.
        _run_git("fetch", "--quiet", "origin", base, cwd=main)
        changed = _branch_changed_files(main, base, branch)
        if changed is None:
            print(f"  경고: base 를 못 찾아 compound 여부를 확인하지 못했어요 ({branch}).")
        else:
            notes = _solution_notes(changed, os.environ.get("HARNESS_DOCS_PATH", "docs"))
            if not notes:
                sys.exit(f"ERROR: compound 미수행 — '{slug}' 는 아무것도 남기지 못해요.\n"
                         "  이 브랜치가 <docs>/solutions/ 를 하나도 건드리지 않았어요.\n"
                         "  /ce-compound 로 교훈을 남긴 뒤 다시 실행하거나,\n"
                         "  남길 게 정말 없으면 --force 로 건너뛰세요.")
            # 도착 판정 — PR 을 볼 수 있으면 그게 정확하다. 못 보면 내용 비교로 폴백한다.
            pr = _pr_status(main, branch)
            if pr is not None:
                state, oids = pr
                tip = _run_git("rev-parse", branch, cwd=main).stdout.strip()
                if state != "MERGED":
                    sys.exit(f"ERROR: PR 이 아직 머지되지 않았어요 (state={state}) — "
                             f"'{slug}' 를 지우면 작업이 사라져요.\n"
                             "  PR 을 머지한 뒤 다시 실행하거나, 정말 버려도 되면 --force 로 건너뛰세요.")
                if tip and tip not in oids:
                    sys.exit(f"ERROR: PR 머지 뒤에 붙은 커밋이 있어요 — '{slug}' 를 지우면 사라져요.\n"
                             f"  로컬 tip {tip[:7]} 이 PR 커밋 목록에 없어요:\n"
                             f"    git log --oneline {oids[-1][:7] if oids else base}..{branch}\n"
                             "  새 PR 로 올려 머지한 뒤 다시 실행하거나, 정말 버려도 되면 --force 로 건너뛰세요.")
            elif not any(_arrived(main, base, branch, p) for p in notes):
                sys.exit(f"ERROR: 교훈이 origin/{base} 에 없어요 — '{slug}' 를 지우면 사라져요.\n"
                         "  남긴 노트: " + ", ".join(notes) + "\n"
                         "  커밋만 하고 push·머지가 안 됐어요. push 한 뒤 PR 을 머지하고 다시 실행하거나,\n"
                         "  정말 버려도 되면 --force 로 건너뛰세요.")

    removed = False
    if wt.exists():
        blocking = _blocking(_run_git("status", "--porcelain", cwd=wt).stdout.splitlines())
        if blocking:
            sys.exit("ERROR: 정리 안 된 변경이 있어요 (아무것도 지우지 않았어요):\n  "
                     + "\n  ".join(blocking))
        shutil.rmtree(wt / "phases", ignore_errors=True)
        r = _run_git("worktree", "remove", str(wt), cwd=main)
        if r.returncode != 0:
            sys.exit(f"ERROR: worktree 제거 실패: {r.stderr.strip()}")
        removed = True
        print(f"  worktree 제거: {wt}")
    else:
        print(f"  worktree 없음 (이미 정리됨): {wt}")
    # `-d` 는 도달 가능성으로 판정하므로 squash 머지면 다 머지됐어도 거부한다.
    # 그래서 실패를 게이트로 쓸 순 없지만, ✓ 로 덮어 버리면 사람이 다음 수순으로 -D 를 밟는다
    # (issue #32 의 실제 피해 경로). 남은 브랜치는 남았다고 말하고 확인 방법을 준다.
    r = _run_git("branch", "-d", branch, cwd=main)
    if r.returncode == 0:
        print(f"  브랜치 {branch} 삭제")
        print(f"  ✓ '{slug}' 정리 완료.")
    else:
        print(f"  ⚠ 브랜치 {branch} 를 남겨뒀어요 — git 이 미머지로 봐요.")
        print("    squash 머지면 정상이지만, 내용을 확인하기 전엔 -D 로 지우지 마세요:")
        print(f"      git diff origin/{base} {branch}")
        print(f"  worktree 만 정리했어요 ('{slug}').")
    if removed:
        # 방금 지운 디렉토리가 셸의 cwd 일 수 있다.
        print(f"  셸이 지워진 경로에 있으면: cd {main}")


def cmd_run(arg):
    """headless: 남은 stage 를 claude -p / 셸로 자동 실행. 실패하면 그 자리에서 멈춘다."""
    f = _resolve(arg)
    doc = _read(f)
    while doc["cursor"] < len(doc["stages"]):
        s = doc["stages"][doc["cursor"]]
        name, action = s["name"], s["action"]
        if name in INTERACTIVE_STAGES:
            # 대화형 stage(discuss/approve)는 사람과의 대화가 곧 실행 — headless 불가.
            sys.exit(f"  ⏸ '{name}' 은 대화형 stage 예요. 대화형 세션에서 진행 후 advance 하세요.")
        if not action.startswith("/"):
            # 명령 stage(commit-push 등)는 메시지·판단이 필요해 headless 자동화 대상이 아님.
            sys.exit(f"  ⏸ '{name}' 은 명령 stage 예요. 직접 실행 후 advance:\n    {action}")
        print(f"  ▶ {name}: {action}")
        prompt = f"{action} — phase '{doc['phase']}' {name} 작업. {s.get('hint', '')}".rstrip()
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
        if name == "implement-red":
            # RED 의 성공 조건(올바른 이유로 실패하는 테스트)은 exit code 로 판정 불가 —
            # 사람이 확인한 뒤 다시 run 으로 이어간다.
            sys.exit("  ⏸ RED 완료 — 테스트가 올바른 이유로 실패하는지 확인 후 다시 run 하세요.")
    print(f"  ✓ '{doc['phase']}' 완료.")


def selftest():
    import io
    from contextlib import redirect_stdout

    doc = new_phase_doc("데모-phase")
    assert doc["branch"] == "데모-PHASE"
    assert doc["cursor"] == 0
    # 기본 doc: TDD on — implement 가 red/green 으로 splice 되어 11개.
    assert [s["name"] for s in doc["stages"]] == [
        "discuss", "plan", "plan-review-ceo", "plan-review-eng", "approve",
        "implement-red", "implement-green", "verify", "commit-push", "make-pr",
        "compound",
    ]
    red, green = doc["stages"][5], doc["stages"][6]
    assert red["action"] == "/ultrawork" and green["action"] == "/ultrawork"
    assert red.get("hint") and green.get("hint")
    assert doc["stages"][0].get("hint", "") == ""  # hint 는 red/green 전용 optional
    for i in range(len(doc["stages"])):
        assert doc["cursor"] == i
        mark_advance(doc, summary=f"s{i}")
    assert doc["cursor"] == len(doc["stages"])
    assert "completed_at" in doc
    assert all(s["status"] == "completed" for s in doc["stages"])
    mark_advance(doc)  # 끝난 뒤 advance 는 no-op
    assert doc["cursor"] == len(doc["stages"])
    no_tdd = new_phase_doc("데모", include_tdd=False)
    names = [s["name"] for s in no_tdd["stages"]]
    assert len(names) == 10 and "implement" in names
    assert "implement-red" not in names and "implement-green" not in names
    no_rev = new_phase_doc("데모", include_review=False)
    assert len(no_rev["stages"]) == 9
    assert not any(s["name"] in REVIEW_STAGES for s in no_rev["stages"])
    no_comp = new_phase_doc("데모", include_compound=False)
    assert len(no_comp["stages"]) == 10
    assert not any(s["name"] == COMPOUND_STAGE for s in no_comp["stages"])
    # 인자 배선 조합 — positional swap 을 잡는다.
    all_off = new_phase_doc("데모", include_review=False, include_compound=False,
                            include_tdd=False)
    assert [s["name"] for s in all_off["stages"]] == [
        "discuss", "plan", "approve", "implement", "verify", "commit-push", "make-pr",
    ]
    # _show_next 출력: 대화형 안내(discuss)와 red hint.
    fresh = new_phase_doc("데모")
    buf = io.StringIO()
    with redirect_stdout(buf):
        _show_next(fresh)
    assert "대화형" in buf.getvalue()
    fresh["cursor"] = 5  # implement-red
    buf = io.StringIO()
    with redirect_stdout(buf):
        _show_next(fresh)
    assert "RED" in buf.getvalue()
    fresh["cursor"] = [s["name"] for s in fresh["stages"]].index("commit-push")
    buf = io.StringIO()
    with redirect_stdout(buf):
        _show_next(fresh)
    assert "일부만 커밋" in buf.getvalue()  # 통째 커밋 대신 범위를 물어본다
    assert _slug("Share Fortune!!") == "share-fortune"
    # worktree 경로 규칙 — init 과 done 이 갈라지면 done 이 엉뚱한 곳을 지운다.
    assert _wt_path(Path("/r"), "a-b") == Path("/r/.claude/worktrees/a-b")
    # 정리 가능 여부 판정: phases/ 만이면 진행, 그 외가 섞이면 그것만 막는다.
    assert _blocking(["?? phases/", "?? phases/x/plan.md"]) == []
    assert _blocking([]) == []
    assert _blocking(["?? phases/x/", " M skills/pipeline/SKILL.md", "?? note.txt"]) == [
        "skills/pipeline/SKILL.md", "note.txt",
    ]
    # compound 게이트 1단(귀속): 이 브랜치가 건드린 <docs>/solutions/ 파일.
    # bool 이 아니라 목록을 돌려줘야 2단(도착 확인)이 그 위에서 돈다 — 필터가 한 곳뿐이다.
    assert _solution_notes(["docs/solutions/foo.md"], "docs") == ["docs/solutions/foo.md"]
    assert _solution_notes(["src/a.py", "docs/solutions/GUARDRAILS.md"], "docs") == [
        "docs/solutions/GUARDRAILS.md",
    ]
    assert _solution_notes(["src/a.py", "docs/ADR.md"], "docs") == []
    assert _solution_notes([], "docs") == []
    # 여러 장을 남긴 경우 전부 — 하나라도 도착하면 통과시키려면 목록이 온전해야 한다.
    assert _solution_notes(["docs/solutions/GUARDRAILS.md", "docs/solutions/a.md"], "docs") == [
        "docs/solutions/GUARDRAILS.md", "docs/solutions/a.md",
    ]
    # docs 경로가 다른 레포도 판정된다 (HARNESS_DOCS_PATH).
    assert _solution_notes(["documentation/solutions/x.md"], "documentation") == [
        "documentation/solutions/x.md",
    ]
    assert _solution_notes(["docs/solutions/x.md"], "documentation") == []
    # 앞뒤 슬래시가 붙어 와도 같은 결과 — env 값을 그대로 받기 때문.
    assert _solution_notes(["docs/solutions/x.md"], "/docs/") == ["docs/solutions/x.md"]
    # solutions 로 시작만 하는 남의 경로를 compound 로 오인하지 않는다.
    assert _solution_notes(["docs/solutions-old/x.md"], "docs") == []
    print("selftest OK")


def main():
    ap = argparse.ArgumentParser(description="Harness Pipeline")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("init"); p.add_argument("name")
    p.add_argument("--no-review", action="store_true", help="plan-review(ceo/eng) stage 생략(안 물어봄)")
    p.add_argument("--no-worktree", action="store_true", help="worktree 없이 현재 체크아웃에서 진행")
    p.add_argument("--no-compound", action="store_true", help="compound stage 생략(/ce-compound 는 수동)")
    p.add_argument("--no-tdd", action="store_true", help="TDD(red/green) 대신 단일 implement stage")
    p = sub.add_parser("status"); p.add_argument("phase", nargs="?")
    p = sub.add_parser("advance"); p.add_argument("phase", nargs="?"); p.add_argument("--summary")
    p = sub.add_parser("run"); p.add_argument("phase", nargs="?")
    p = sub.add_parser("done"); p.add_argument("phase")
    p.add_argument("--force", action="store_true", help="compound 미수행이어도 정리 강행")
    sub.add_parser("selftest")
    a = ap.parse_args()

    if a.cmd == "init":
        cmd_init(a.name, a.no_review, a.no_worktree, a.no_compound, a.no_tdd)
    elif a.cmd == "status":
        cmd_status(a.phase)
    elif a.cmd == "advance":
        cmd_advance(a.phase, a.summary)
    elif a.cmd == "run":
        cmd_run(a.phase)
    elif a.cmd == "done":
        cmd_done(a.phase, a.force)
    elif a.cmd == "selftest":
        selftest()


if __name__ == "__main__":
    main()
