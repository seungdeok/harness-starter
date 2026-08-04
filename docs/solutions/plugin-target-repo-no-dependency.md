# 플러그인이 대상 레포에 뿌리는 해법은 런타임 의존을 만들지 않는 쪽으로 고른다

- 날짜: 2026-08-01
- 작업/PR: [#19](https://github.com/seungdeok/harness-starter/pull/19) (이슈 [#11](https://github.com/seungdeok/harness-starter/issues/11)), 브랜치 `SETUP-GITIGNORE-PLAN`

## 문제

이슈 #11: `/harness:setup` 이 대상 레포 `.gitignore` 에 `phases/` 를 통째로 넣어서 `phases/<slug>/plan.md` 가 영구히 무시됐다. ADR-004 는 plan.md 를 커밋 대상으로 만들어 놨으니 setup 과 pipeline 이 서로 어긋난 상태였다.

고치는 과정에서 **방향이 두 번 바뀌었다.** 최종안에 도달하기까지 discuss 결론을 두 번 폐기했다.

| # | 방향 | 폐기 사유 | 누가 잡았나 |
| --- | --- | --- | --- |
| 1 | `phases/*/*` + `!phases/*/plan.md` 두 줄로 맞추기 | 증상 패치. 규칙 전파 부담이 그대로 남음 | plan-review-eng |
| 2 | lefthook pre-commit 으로 차단 | **대상 레포에 lefthook 이 있을 리 없음** | 사용자 |
| 3 | `phases/` 를 커밋 대상에서 빼고 무시 규칙 자체를 제거 | 채택 | — |

## 원인

**2번이 후보에 오른 게 이 작업의 실제 미스다.**

lefthook 안이 처음 나왔을 때 "harness 는 임의의 대상 레포에 설치되는 플러그인이라 설치처에 lefthook 이 있다고 가정할 수 없다"고 근거를 대서 반대했다. 그런데 사용자가 그래도 lefthook 을 원하자, **단점을 옵션 설명에 적어두는 것으로 갈음하고 선택지 목록에 다시 올렸다.** 사용자는 그걸 골랐고, discuss stage 를 그 결론으로 advance 했다.

그다음에야 "플러그인 설치하는 곳에서 lefthook 을 설치할 리가 없잖아" 라는 지적이 왔다 — 내가 처음에 댄 반대 근거와 같은 내용이다.

즉 근거를 못 찾아서 틀린 게 아니라, **근거를 이미 갖고 있으면서 결정적 제약을 "선호 문제"로 격하시킨 것**이다. 설치처에 의존이 없다는 건 취향이 아니라 이 프로젝트의 배포 모델(ADR-002: 레포=plugin=marketplace)이 강제하는 제약이다.

## 해결

`phases/<slug>/` 하위 전체(plan.md 포함)를 커밋 대상에서 빼고, `.gitignore` 규칙도 두지 않는다. 방침은 CLAUDE.md §6 규범으로만 강제한다.

무시 규칙을 고치는 대신 없애니 대상 레포에 전파할 규칙 자체가 사라진다 — `/harness:setup` 의 gitignore 블록은 `.claude/worktrees/` + `.claude/settings.local.json` 두 줄로 줄었다. (ADR-005, ADR-004 의 plan.md 커밋 대상화 조항 대체)

트레이드오프로 `phases/` 가 `git status` 에 항상 untracked 로 뜬다. CLAUDE.md §6 의 `git add .` 금지와 commit-push stage 의 범위 확인 절차로 막는다.

## 재발 방지

**근거를 대서 배제한 안을 다시 선택지에 올릴 때는, 그 근거가 선호 문제인지 제약인지 먼저 구분한다.** 제약이면 옵션에서 빼거나 "이건 못 고른다"고 말한다. 단점을 옵션 설명에 적어두는 건 제약을 선호로 격하시키는 것과 같다.

이 프로젝트에 한정한 형태: **harness 가 대상 레포에 뿌리는 것(gitignore 줄, 훅, 스크립트, CI)은 대상 레포에 런타임 의존을 만들지 않아야 한다.** 대상 레포의 언어·툴체인을 모르는 게 기본값이다.

→ [GUARDRAILS.md](GUARDRAILS.md) 에 승격.

## 부수 교훈 — 미러 파일은 계획에 안 잡히면 verify 에서 잡아야 한다

`skills/setup/templates/CLAUDE-section.md` 는 루트 `CLAUDE.md` 의 §1–5 를 그대로 미러링해서 대상 레포에 뿌리는 파일이다. 그런데 plan 단계에서 변경 파일 목록을 뽑을 때 이 파일이 빠졌다.

gitignore 줄을 뺀 뒤 §6 규범을 CLAUDE.md 에만 넣었다면, **대상 레포는 무시 규칙도 없고 규범도 없는 상태**가 됐을 것이다 — `git add .` 한 번이면 phase.json 이 커밋된다. 원래 버그보다 나쁜 상태다.

verify stage 에서 grep 으로 잡아 보완했고, 두 §6 이 `diff` 로 동일한지 확인했다. 계획에 없던 파일이라 "계획대로 했는지" 만 봤으면 통과했을 것이다 — **verify 는 계획 이행이 아니라 수용 기준 충족을 봐야 한다**는 게 확인됐다.

→ [GUARDRAILS.md](GUARDRAILS.md) 에 승격.
