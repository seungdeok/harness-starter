---
title: "git diff scope and merge conflict precheck — PR 범위·충돌 사전 검사"
tags: ["git", "diff", "merge", "worktree", "pr"]
created: 2026-08-01T14:25:43.146Z
updated: 2026-08-01T14:25:43.146Z
sources: []
links: ["worktree-phase-traps-cwd.md", "pipeline-phase-slug-stage-worktree.md"]
category: reference
confidence: medium
schemaVersion: 1
---

# git diff scope and merge conflict precheck — PR 범위·충돌 사전 검사

PR 범위를 잘못 읽거나 충돌을 늦게 아는 걸 막는 실전 레퍼런스. 근거: `docs/solutions/pr-scope-two-dot-diff.md` (PR #23)

## 두 점과 세 점은 `log` 와 `diff` 에서 뜻이 반대다

| 표기 | `git log` | `git diff` |
| --- | --- | --- |
| `A..B` | B 에만 있는 커밋 (merge-base 기준) | A 와 B **두 tip** 비교 |
| `A...B` | 양쪽 대칭차 | **merge-base(A,B) 와 B** 비교 |

**GitHub 이 PR diff 로 보여주는 건 `A...B`** 다.

그래서 `git log main..HEAD` 와 `git diff main..HEAD` 를 나란히 놓고 읽으면 기준이 서로 달라 숫자가 안 맞는다. 실제 사례: 커밋은 1개인데 파일이 7개로 보였다 — `origin/main` 이 세션 중 3커밋 전진했고 그 커밋들이 **역방향 변경으로 섞여** 보인 착시였다. PR 에 실제로 보일 diff 는 처음부터 1파일이었다.

착시를 걷어낸 뒤에야 **진짜 충돌**이 드러났다. 전진한 커밋 하나가 같은 섹션을 건드리고 있었고, 그때는 이미 push 한 뒤였다.

## 판단 기준 ref 는 로컬 브랜치가 아니라 `origin/<base>`

worktree 에서 작업하는 동안 아무도 `main` 을 체크아웃하지 않으므로 **로컬 `main` 은 며칠씩 안 움직인다.** 보기 전에 반드시 fetch 한다.

드문 일이 아니다: 작업 하나를 하는 동안 `origin/main` 이 **세 번** 전진한 기록이 있다.

## 표준 절차 — 커밋 전에 돌린다

```bash
git fetch origin <base> -q                       # 로컬 ref 를 믿지 않는다

git diff --stat origin/<base>...HEAD             # 세 점 — PR 에 실제로 보일 diff

git merge-tree --write-tree origin/<base> HEAD >/dev/null \
  && echo "충돌 없음" || echo "충돌 있음"
```

`git merge-tree --write-tree` 는 **체크아웃도 머지도 하지 않고 exit code 로만** 알려준다. 작업트리를 안 건드리므로 커밋 전 아무 때나 부담 없이 돌릴 수 있다.

## 왜 파이프라인이 이걸 늦게 잡는가

`commit-push` stage 는 origin 상태를 보지 않고 push 하고, `make-pr` 에 와서야 base 를 본다. 즉 **이미 머지 불가능한 브랜치를 push 한 뒤** 충돌을 알게 된다. 그래서 위 절차를 `commit-push` **전에** 끼워 넣는다.

## 이미 push 한 브랜치의 충돌은 merge 로 푼다

rebase 는 force-push 를 요구하는데, **이 환경의 pre-tool hook 이 `git push --force` 를 (`--force-with-lease` 포함) 차단한다.** push 이력을 다시 쓰지 않는 merge 가 제약 안에서의 답이다.


## 관련
[[worktree-phase-traps-cwd]] · [[pipeline-phase-slug-stage-worktree]]
