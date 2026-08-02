---
name: pipeline
description: >
  한 작업(phase)을 discuss → plan → [plan-review-ceo] → [plan-review-eng] → approve →
  implement-red → implement-green (TDD, 기본) | implement (--no-tdd) → verify →
  commit-push → make-pr 순서로 돌리는 반자동 파이프라인을 시작·진행해요. 다음 상황에서
  활성화돼요: 사용자가 "파이프라인 돌려줘", "파이프라인 시작", "phase 시작",
  "새 작업 시작해줘", "작업 파이프라인", "run pipeline", "start phase"라고 말할 때.
  시작 전에 worktree 사용 여부·plan review 범위·TDD 여부를 물어봐요.
  compound(교훈 기록)는 포함하지 않아요 — 그건 `/ce-compound` 로 수동 실행이에요.
argument-hint: "[phase 이름]"
user-invocable: true
metadata:
  author: seungdeok
---

# pipeline

`pipeline.py` 를 몰아서 한 phase 를 **discuss 부터 make-pr 까지** 진행해요.
compound(CLAUDE.md 5장)는 안 해요 — 파이프라인이 끝나면 사용자가 `/ce-compound` 로 직접 남겨요.

Stages: `discuss → plan → [plan-review-ceo] → [plan-review-eng] → approve → implement-red → implement-green (TDD, 기본) | implement (--no-tdd) → verify → commit-push → make-pr`

## 스크립트 위치 (먼저 결정)

아래 규칙으로 `pipeline.py` 경로를 정하고, 이후 모든 명령에서 그 경로를 써요:

1. 환경변수 `HARNESS_SCOPE` 를 확인하고, 없으면 프로젝트의 `.claude/settings.local.json` 의 `env.HARNESS_SCOPE` 를 읽어요. 값이 `project` 이고 `<프로젝트>/scripts/pipeline.py` 가 있으면 → **그 파일**을 사용.
2. 그 외(글로벌 scope, 또는 값 없음) → **이 스킬 폴더의 `scripts/pipeline.py`(번들)** 를 절대 경로로 사용.
3. `HARNESS_SCOPE` 값이 어디에도 없으면 `/harness:setup` 을 먼저 실행하라고 권한 뒤, 사용자가 원하면 번들 스크립트 + 기본값으로 그냥 진행해도 돼요.

스크립트는 **cwd 기준 git root** 에 phase 를 만들므로, 어느 복사본이든 실행 위치(cwd)가 곧 대상 레포예요.

## 0. 시작 전 점검과 질문 (필수)

### 0-1. 하드 의존 스킬 점검

`init` 은 worktree·브랜치를 먼저 만들기 때문에, 스킬 누락을 stage 도달 시점에 발견하면 이미 늦어요.
**init 전에** 사용 가능한 스킬 목록에서 아래를 확인해요. 목록에 뜨는 식별자 그대로 찾아요 — OMC 는
`oh-my-claudecode:` 접두어가 붙고, gstack 은 프로젝트 `.claude/skills/` 에 있어 접두어가 없어요.

| stage | 스킬 | 목록상 이름 | 없을 때 |
| --- | --- | --- | --- |
| plan | `/plan` | `oh-my-claudecode:plan` | 대안 없음 |
| implement(-red/-green) | `/ultrawork` | `oh-my-claudecode:ultrawork` | 대안 없음 |
| verify | `/verify` | `oh-my-claudecode:verify` | 대안 없음 |
| plan-review-ceo | `/plan-ceo-review` | `plan-ceo-review` | `--no-review` |
| plan-review-eng | `/plan-eng-review` | `plan-eng-review` | `--no-review` |

- **OMC 스킬이 하나라도 없으면** 어느 stage 가 막히는지 알리고, AskUserQuestion 으로
  `설치 후 다시 시작 / 그대로 진행` 을 물어요. 임의로 init 을 강행하지 않아요.
- **gstack 스킬이 없으면** 아래 plan review 질문을 **묻지 않고** `--no-review` 로 고정해요.
  고를 수 없는 걸 선택지에 남기지 않아요.

### 0-2. 시작 전 질문

`init` 하기 **전에 AskUserQuestion 으로 세 가지를 먼저** 물어요.

1. **worktree** — 이 phase 를 어디서 돌릴지
   - `전용 worktree` (기본, 병렬 안전): `.claude/worktrees/<slug>` 에 새 브랜치로 격리 → `init` 에 플래그 없음
   - `현재 체크아웃`: 지금 브랜치에서 바로 → `init --no-worktree`
2. **plan review** — 계획 검토를 어디까지 할지
   - `CEO + Eng 둘 다` (기본) → 플래그 없음
   - `CEO 만` / `Eng 만` → 둘 다 넣되(플래그 없음) 원치 않는 review stage 에서 실행 없이 `advance`
   - `생략` → `init --no-review`
3. **TDD** — implement 를 RED/GREEN 두 stage 로 나눌지
   - `yes` (기본) → 플래그 없음
   - `no` → `init` 에 `--no-tdd` 를 늘 명시적으로 전달

답을 받은 뒤 그에 맞는 플래그로 init 해요. **compound 는 항상 빼니 `--no-compound` 를 늘 붙여요.**

## 1. phase 시작

phase 이름이 인자로 없으면 사용자에게 물어요. 그다음:

```bash
python3 <pipeline.py 경로> init "<phase 이름>" --no-compound [--no-worktree] [--no-review] [--no-tdd]
```

- 브랜치 이름은 입력한 이름(slug)을 대문자로 한 것 (예: "share fortune" → `SHARE-FORTUNE`). pipeline.py 가 알아서 만들어요.
- 전용 worktree 를 만들었으면 **이후 모든 명령은 그 worktree 안(cwd)에서** 실행해요:

```bash
cd .claude/worktrees/<slug>
```

## 2. stage 루프 (discuss → make-pr)

`status` 로 지금 stage 를 확인하고, 그 stage 를 이 세션에서 실행한 뒤 `advance` 로 넘어가요. **make-pr 까지 반복.**

```bash
python3 <pipeline.py 경로> status
```

- **스킬 stage** (`/plan`, `/plan-ceo-review`, `/plan-eng-review`, `/ultrawork`, `/verify`, `/make-pr`)
  → 그 스킬을 실행하고, 결과가 만족스러우면 `advance`.
- **명령 stage** (`commit-push`)
  → 변경분을 통째로 커밋하지 말고 **범위를 먼저 확인받아요**: `git status --short`/`git diff --stat` 요약과 제안 커밋 메시지를 보여준 뒤 AskUserQuestion 으로 `이대로 전체 커밋 / 일부만 커밋 / 직전 커밋에 합치기(amend) / 건너뛰기` 중 하나를 고르게 해요. 여러 stage 의 변경을 한 커밋으로 합쳐야 할 때가 있어서예요. 커밋 메시지는 Conventional Commits (`feat(<slug>): <뭐 했는지>`). git-master 위임 권장. 커밋·푸시 후 `advance` (건너뛰기면 커밋 없이 `advance`).
- **stage 별 실행법**:
  - `discuss` (대화형): 이슈·요구사항을 자유 대화로 정리하고, 핵심 합의를 `advance --summary` 에 기록해요. 범위가 phase 이름·TDD 선택과 어긋나게 바뀌면 새 이름으로 재-init 해요(기존 worktree 정리 후); TDD 플래그를 바꿀 때도 재-init 해요.
  - `plan`: 계획을 `phases/<slug>/plan.md` 에 저장해요(approve·verify 의 기준 문서 — 로컬 작업 산출물이라 커밋하지 않아요).
  - `approve` (대화형): `phases/<slug>/plan.md` 를 AskUserQuestion 으로 승인받아요. 거절되면 cursor 롤백 없이 그 자리에서 문서를 수정하고 다시 승인받아요.
  - `implement-red`: 실패하는 테스트만 작성하고, 올바른 이유로 실패하는지 확인한 뒤 `advance`. 구현 코드는 작성하지 않아요.
  - `implement-green`: 최소 구현으로 테스트를 통과시킨 뒤 `advance`. red 에서 만든 테스트를 수정해서 통과시키는 건 금지예요.
  - `verify`: `/verify` 로 검증해요. 테스트 통과를 재확인하는 게 아니라 `plan.md` 의 수용 기준과 실제 동작을 증거로 검증해요(green 과 구별되는 기준).
- **CEO만/Eng만 하기로 한 경우** → 원치 않는 review stage 에서는 스킬을 실행하지 말고 그냥 건너뛰어요:
  `python3 <pipeline.py 경로> advance --summary "생략"`

```bash
python3 <pipeline.py 경로> advance --summary "<이 stage 에서 한 일>"
```

진행 중 phase 가 하나면 `status`/`advance` 는 인자 없이 자동 인식, 여러 개면 이름을 줘요.

## 3. make-pr 후 종료 (compound 는 수동)

make-pr stage 를 `advance` 하면 파이프라인은 여기서 끝이에요. **compound 는 자동으로 하지 않아요.**
마지막에 사용자에게 이렇게 안내하고 마쳐요:

> 파이프라인 완료(make-pr까지). 교훈을 남기려면 `/ce-compound` 를 직접 실행하세요.

전용 worktree 를 썼다면 **PR 이 머지된 뒤** 정리도 안내해요 (안 하면 worktree·브랜치가 계속 쌓여요):

```bash
cd <메인 레포 루트> && python3 <pipeline.py 경로> done <slug>
```

`done` 은 worktree 를 지우고 `git branch -d` 로 브랜치를 정리해요. `-d` 는 도달 가능성으로 판정해서
**squash 머지면 다 머지됐어도 거부**해요 — 그래서 브랜치가 남는 건 흔한 정상 상황이고, 그럴 땐
`✓ 정리 완료` 대신 확인 명령(`git diff origin/<base> <branch>`)을 안내해요. 확인 전에 `-D` 로 지우지 마세요.
`phases/<slug>/` 외에 커밋 안 된 변경이 남아 있으면 아무것도 지우지 않고 멈춰요.

**`done` 은 교훈이 `origin/<base>` 에 **도착**했는지 먼저 확인해요.** 두 단계로 봐요:

1. 그 브랜치가 `<docs>/solutions/` 를 하나도 안 건드렸으면 → `compound 미수행` 으로 거부.
2. 건드렸어도 그 노트가 `origin/<base>` 에 없으면(커밋만 하고 push·머지 안 됨) → 거부.

둘 다 **아무것도 지우지 않아요** — worktree 가 사라지면 그 작업은 아무것도 남기지 못하니까요.
그러니 정리 **전에** `/ce-compound` 를 돌리고, 그 커밋을 push 해서 머지까지 끝내요.
남길 게 정말 없으면 `done <slug> --force` 로 건너뛰어요.
origin 이 없어 base 를 못 찾는 레포에서는 차단 대신 경고만 하고 진행해요.

교훈 중 재발 방지 규칙이 강제가 꼭 필요한 경우에만 Claude Code hook 으로도 승격해요.

## 주의

- 전용 worktree 를 만든 경우, 모든 `status`/`advance` 는 그 worktree 안에서 실행해야 `phase.json` 을 찾아요.
- stage 가 실패하면 그 자리에서 멈추고, 고친 뒤 `status` 부터 다시.
- phase.json(`phases/<slug>/phase.json`)이 어느 stage 까지 왔는지 기억하므로, 중간에 끊겨도 이어서 진행할 수 있어요.
- headless `run` 은 새 phase 를 처음부터 자동으로 끝까지 돌리는 게 아니라 **resume 전용** 헬퍼예요 — discuss·approve·implement-red 처럼 사람 확인이 필요한 stage 에서는 멈춰요.
