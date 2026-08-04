# 외부 도구의 제약은 계획 전에 실측하고, 그 probe 는 디렉토리 단위로 지우지 않는다

- 날짜: 2026-08-01
- 작업/PR: [#22](https://github.com/seungdeok/harness-starter/pull/22) (이슈 [#14](https://github.com/seungdeok/harness-starter/issues/14)), 브랜치 `WORKTREE-CLEANUP`

## 문제

issue #14 — phase 를 돌릴수록 `.claude/worktrees/<slug>` 와 로컬 브랜치가 쌓이는데 정리 경로가 없었다.
해법은 명백해 보였다: `pipeline.py done <phase>` 가 `git worktree remove` + `git branch -d` 를 부르면 끝.

그런데 **문서만 보고 그대로 썼으면 정상 경로가 100% 실패하는 기능이 나왔을 것이다.**

## 원인

### 1. 실측이 설계를 두 번 바꿨다

plan stage 전에 임시 worktree 를 만들어 실제로 돌려봤고, 그 자리에서 두 가지가 드러났다.

| probe | 결과 | 설계에 미친 영향 |
| --- | --- | --- |
| untracked 파일이 있는 worktree 에 `git worktree remove` | `fatal: ... contains modified or untracked files, use --force` | **모든** phase worktree 는 `phases/<slug>/`(untracked, ADR-005)를 갖고 있다 → 그냥 `remove` 하면 항상 실패. `phases/` 를 먼저 지우는 단계가 필수가 됐다 |
| worktree 안에서 `git rev-parse --git-common-dir` | `../.git` (상대 경로) | `--path-format=absolute`(git 2.31+) 대신 `.resolve()` 로 충분. 옵션 하나가 빠지고 호환 범위가 넓어짐 |

`--force` 를 기본으로 붙이는 게 "간단한" 해법처럼 보였지만, 그건 커밋 안 한 실제 작업을 조용히 날리는 경로다. 실측이 없었으면 그 함정이 안 보였다.

### 2. verify 는 재확인이 아니라 새 결함 발견 단계였다

plan 과 plan-review-eng 를 통과한 뒤 verify 에서 실제로 돌려보다가 결함이 하나 더 나왔다.
`cmd_init` 은 `ROOT`(현재 체크아웃) 기준으로 worktree 를 만드는데 `cmd_done` 은 메인 체크아웃 기준으로 찾는다.
worktree 안에서 `init` 하면 `<worktree>/.claude/worktrees/` 에 중첩 생성돼 `done` 이 영원히 못 찾는다.

경로 규칙을 `_wt_path()` 로 공유했는데도 **기준점(base)이 갈라져 있어서** 규칙 공유가 무의미했다. 코드를 읽어서는 안 보이고 돌려봐야 보이는 종류다.

### 3. probe 를 지우다 추적 파일을 날렸다

중첩 생성된 `<worktree>/.claude/worktrees/zz-nested` 를 정리하면서 부모인 `<worktree>/.claude` 를 통째로 `shutil.rmtree` 했다.
그 디렉토리에는 **추적 중인 파일**이 같이 있었다 — `.claude/settings.json`, `.claude/skills/plan-ceo-review/**`, `.claude/skills/plan-eng-review/**` (총 4,600여 줄).

`git status` 에서 대량 삭제로 잡혀 `git checkout -- .claude/` 로 복구했지만, 커밋 직전에 diff 를 안 봤으면 그대로 PR 에 실렸다.
원인은 단순하다: **지우려던 건 자식 하나인데 부모 디렉토리를 지웠다.**

## 해결

- `done` 은 `phases/` 를 지우기 전에 `git status --porcelain` 으로 먼저 확인하고, `phases/` 외 변경이 있으면 **아무것도 지우지 않는다** (`_blocking()` 순수 함수 + selftest).
- `cmd_init` 도 `_main_root()` 기준으로 통일 — 기준점까지 공유해야 경로 규칙 공유가 의미가 있다.
- 지운 추적 파일은 `git checkout -- .claude/` 로 복구, 최종 diff 가 의도한 2파일(`+83 -3`)뿐인지 커밋 전에 확인.

## 재발 방지

- **외부 도구(git·CLI·SDK)의 실패 조건에 설계가 걸려 있으면 plan 전에 임시 리소스로 한 번 돌려본다.** 문서에 안 적힌 거부 조건이 정상 경로를 통째로 막을 수 있다.
- **probe 산출물을 지울 때는 만든 것만 지운다.** 부모 디렉토리 `rmtree` 는 그 안의 추적 파일까지 가져간다. 지운 뒤 `git status` 로 예상 밖 삭제가 없는지 본다.
- verify 는 "테스트가 또 통과하나" 가 아니라 "계획이 못 본 게 있나" 를 보는 단계로 쓴다. 이번엔 실제로 결함 하나를 더 잡았다.

관련: [ci-check-coverage.md](ci-check-coverage.md) (검사 도구는 일부러 깨뜨려 확인한다 — 이번에도 `_blocking`·`_wt_path` 를 파손해 `exit 1` 을 확인했다), [ARCHITECTURE.md](../ARCHITECTURE.md)
