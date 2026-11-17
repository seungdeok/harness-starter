#!/usr/bin/env python3
"""PreToolUse(Bash) guard: 규범으로만 적혀 있던 git·검증 규칙을 실행 직전에 강제 (ADR-016).

근거: https://tech.kakaopay.com/post/ai-agent-2/
  - 파이프로 검증 실패가 통과로 둔갑 (`pnpm lint | tail -20` → exit 0)
  - `git stash && lint && git stash pop` 으로 다른 세션 작업 유실
  - CLAUDE.md §6: phases/ 는 커밋하지 않고, git add -A / . 로 쓸어 담지 않는다
의존: python3 stdlib 만 (jq 불필요). 대상 레포에는 아무것도 설치하지 않는다.
Self-check: python3 hooks/bash-guard.py --test
"""
import json
import re
import sys

# 실행기로 시작하는 세그먼트만 검증 명령으로 본다 (grep test ... | head 같은 오탐 방지)
VERIFY = (r"(?:^|[;&(]|\bthen|\bdo)\s*(?:rtk\s+)?"
          r"(?:npm|pnpm|yarn|bun|npx|make|cargo|go|uv|poetry|python3?\s+-m|tsc|vitest|jest|pytest|eslint|biome)\b"
          r"[^|;&]*\b(?:lint|test|tsc|typecheck|type-check|check|vitest|jest|pytest|eslint|biome|build|--noEmit)\b")
RULES = [
    # (pattern, reason) — 마지막 항목(파이프)은 pipefail 이 있으면 건너뛴다
    (r"\bgit\s+stash(?!\s+(list|show)\b)",
     "git stash 금지: 실패 시 변경이 stash 에 남아 다른 세션 작업이 유실돼요. 변경 파일만 대상으로 검증하세요."),
    (r"\bgit\s+restore\b(?!.*--staged)(?!.*--source)",
     "git restore(워킹트리) 금지: 커밋 안 된 변경을 되돌릴 수 없게 지워요. 필요하면 사용자에게 확인받으세요."),
    (r"\bgit\s+restore\b(?=.*--worktree)",
     "git restore --worktree 금지: 커밋 안 된 변경이 지워져요."),
    (r"\bgit\s+clean\b",
     "git clean 금지: untracked 파일(phases/ 등 로컬 산출물)이 삭제돼요."),
    (r"\bgit\s+reset\b.*--hard",
     "git reset --hard 금지: 커밋 안 된 변경이 사라져요."),
    (r"\bgit\s+checkout\s+(--\s+)?\.(\s|$)",
     "git checkout . 금지: 워킹트리 변경이 사라져요."),
    (r"\bgit\s+add\b.*(\s|^)(-A|--all|\.)(\s|$)",
     "git add -A / . 금지: phases/ 산출물이 섞여요. 커밋할 파일을 명시하세요 (CLAUDE.md §6)."),
    (r"\bgit\s+add\b.*(phases/|\.omc/)",
     "phases/, .omc/ 는 로컬 산출물이라 커밋 금지 (ADR-005, ADR-011)."),
    (VERIFY + r"[^|;&]*\|(?!\|)",
     "검증 명령에 파이프 금지: 종료 코드가 파이프 마지막 명령(tail 등)으로 바뀌어 실패가 통과로 기록돼요. 파이프 없이 다시 실행하세요."),
]


def check(cmd: str):
    cmd = re.sub(r"\d*>&\d*", " ", cmd)  # 2>&1 의 & 가 명령 구분자로 읽히지 않게
    rules = RULES[:-1] if "pipefail" in cmd else RULES
    for pat, reason in rules:
        if re.search(pat, cmd, re.IGNORECASE | re.DOTALL):
            return reason
    return None


def main():
    data = json.load(sys.stdin)
    reason = check(data.get("tool_input", {}).get("command", ""))
    if reason:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"[harness bash-guard] {reason}",
        }}, ensure_ascii=False))


def _test():
    deny = [
        "git stash && pnpm lint && git stash pop",
        "git restore src/a.ts",
        "git restore --worktree --staged .",
        "git clean -fd",
        "git reset --hard HEAD",
        "git checkout -- .",
        "git add -A",
        "git add .",
        "git add phases/foo/phase.json",
        "pnpm lint | tail -20",
        "npx tsc --noEmit 2>&1 | head",
        "npm test | grep FAIL",
        "cd app && pnpm test | tail",
        "uv run pytest -x | tail -5",
    ]
    allow = [
        "git stash list",
        "git restore --staged src/a.ts",
        "git reset HEAD~1",
        "git add src/a.ts src/b.ts",
        'git commit -m "feat: add guard"',
        "pnpm lint",
        "pnpm lint || echo failed",
        "set -o pipefail; pnpm lint | tail -20",
        "ls | head",
        "git log --oneline | head",
        "echo lint | tail -1",
        "grep -rn test src | head",
        "cat build.log | tail",
    ]
    for c in deny:
        assert check(c), f"should deny: {c}"
    for c in allow:
        assert not check(c), f"should allow: {c} ({check(c)})"
    print("ok")


if __name__ == "__main__":
    _test() if "--test" in sys.argv else main()
