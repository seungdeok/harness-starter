---
date: 2026-08-01
track: knowledge
category: workflow-issues
title: "PR 범위는 origin 기준 three-dot 으로 본다 — 긴 세션에서 두 tip 비교는 남의 커밋을 내 diff 로 보여준다"
tags: [git, worktree, pipeline, make-pr, merge-base, conflict]
---

# PR 범위는 origin 기준 three-dot 으로 본다 — 긴 세션에서 두 tip 비교는 남의 커밋을 내 diff 로 보여준다

- 날짜: 2026-08-01
- 작업/PR: [#23](https://github.com/seungdeok/harness-starter/pull/23) (이슈 [#16](https://github.com/seungdeok/harness-starter/issues/16)), 브랜치 `PIPELINE-SOURCE-SHA`

## 문제

`make-pr` stage 에서 스킬이 시키는 대로 변경 파일을 확인했다:

```bash
git log main..HEAD --oneline      # → 커밋 1개
git diff --name-only main..HEAD   # → 파일 7개
```

커밋은 1개인데 파일이 7개. 내 변경이 계획(1파일)을 훨씬 넘긴 것처럼 보였다.

실제로는 두 가지가 겹쳐 있었다.

1. **7파일은 착시였다.** `git diff A..B` 는 이름과 달리 `A` 와 `B` 두 **tip 을 비교**한다(`git diff A B` 와 동일).
   세션 도중 `origin/main` 이 3커밋 전진해 있었고, 그 커밋들이 **역방향 변경으로 섞여** 보인 것이다.
   PR 에 실제로 보일 diff 는 처음부터 1파일이었다.
2. **그런데 진짜 문제가 그 뒤에 있었다.** 전진한 커밋 중 하나(#13)가 내가 고친 것과 **같은 섹션**을 건드려
   실제 머지 충돌이 있었다. 착시를 걷어낸 뒤에야 발견했고, 그때는 이미 브랜치를 push 한 뒤였다.

## 원인

**두 점(`..`)과 세 점(`...`)이 `log` 와 `diff` 에서 뜻이 반대다.**

| 표기 | `git log` | `git diff` |
| --- | --- | --- |
| `A..B` | B 에만 있는 커밋 (merge-base 기준) | A 와 B **두 tip** 비교 |
| `A...B` | 양쪽 대칭차 | **merge-base**(A,B) 와 B 비교 |

GitHub 이 PR diff 로 보여주는 건 `A...B` 다. 그래서 `git log A..HEAD` 와 `git diff A..HEAD` 를
나란히 놓고 읽으면 두 명령의 기준이 서로 달라 숫자가 안 맞는다.

여기에 두 가지가 더 겹쳤다:

- **로컬 `main` 이 낡았다.** worktree 에서 작업하는 동안 아무도 `main` 을 체크아웃하지 않으니
  로컬 `main`(`3348173`)은 `origin/main`(`15cbb93`)보다 뒤처져 있었다. 판단 기준으로 쓸 수 없는 ref 였다.
  드문 일이 아니다 — 이 작업 하나를 하는 동안 `origin/main` 은 **세 번** 전진했고(`f174d04` → `15cbb93` → `c7ab9c6`),
  마지막 한 번은 이 노트를 쓰는 중에 일어났다.
- **파이프라인 stage 순서상 늦게 발견된다.** `commit-push` 는 origin 상태를 안 보고 push 하고,
  `make-pr` 에 와서야 base 를 본다. 즉 **이미 머지 불가능한 브랜치를 push 한 뒤** 충돌을 알게 된다.

## 해결

범위 확인과 충돌 검사를 **`origin/<base>` 기준으로, 커밋하기 전에** 한다.

```bash
git fetch origin <base> -q                       # 로컬 ref 를 믿지 않는다

git diff --stat origin/<base>...HEAD             # ← 세 점. PR 에 실제로 보일 diff

git merge-tree --write-tree origin/<base> HEAD >/dev/null \
  && echo "충돌 없음" || echo "충돌 있음"          # 작업트리를 건드리지 않는 충돌 검사
```

`git merge-tree --write-tree` 는 체크아웃도 머지도 하지 않고 exit code 로만 알려주므로,
커밋 전 아무 때나 부담 없이 돌릴 수 있다.

이번엔 충돌 해소를 **rebase 가 아니라 merge** 로 했다. 브랜치를 이미 push 한 상태였고
rebase 는 force-push 를 요구하는데, 이 환경의 pre-tool hook 이 `git push --force` 를
(`--force-with-lease` 포함) 차단한다. push 이력을 다시 쓰지 않는 merge 가 제약 안에서의 답이었다.

## 재발 방지

- PR 범위는 항상 `git diff origin/<base>...HEAD` (세 점)로 본다. `git log A..B` 와 `git diff A..B` 는
  기준이 반대라 나란히 읽으면 안 된다.
- 판단 기준 ref 는 로컬 브랜치가 아니라 `origin/<base>` 다. 보기 전에 `git fetch` 한다 —
  worktree 에서는 로컬 `main` 이 며칠씩 안 움직인다.
- 긴 세션(1시간 이상)이나 worktree 작업은 **커밋 직전에** `git merge-tree --write-tree origin/<base> HEAD`
  로 충돌을 미리 본다. 충돌은 push 전에 아는 게 싸다.
- 이미 push 한 브랜치의 충돌은 merge 로 해소한다. rebase 는 force-push 를 부르고,
  이 환경에선 hook 이 막는다.

관련: 이번 작업의 설계 결정은 `docs/ADR.md` ADR-008 에, worktree 에서 cwd 를 놓치는 다른 함정은
[pipeline-worktree-cwd.md](pipeline-worktree-cwd.md) 에 있다.
