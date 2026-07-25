---
name: pipeline
description: >
  한 작업(phase)을 plan → plan-review → implement → commit-push → make-pr 순서로 돌리는
  반자동 파이프라인을 시작·진행해요. 다음 상황에서 활성화돼요: 사용자가 "파이프라인 돌려줘",
  "파이프라인 시작", "phase 시작", "새 작업 시작해줘", "작업 파이프라인", "run pipeline",
  "start phase"라고 말할 때. 시작 전에 worktree 사용 여부와 plan review 범위를 물어봐요.
  compound(교훈 기록)는 포함하지 않아요 — 그건 `/ce-compound` 로 수동 실행이에요.
argument-hint: "[phase 이름]"
user-invocable: true
metadata:
  author: seungdeok
---

# pipeline

`pipeline.py` 를 몰아서 한 phase 를 **plan 부터 make-pr 까지** 진행해요.
compound(CLAUDE.md 5장)는 안 해요 — 파이프라인이 끝나면 사용자가 `/ce-compound` 로 직접 남겨요.

Stages: `plan → [plan-review-ceo] → [plan-review-eng] → implement → commit-push → make-pr`

## 스크립트 위치 (먼저 결정)

아래 규칙으로 `pipeline.py` 경로를 정하고, 이후 모든 명령에서 그 경로를 써요:

1. 프로젝트의 `.claude/harness.json` 을 읽어요. `scope` 가 `project` 이고 `<프로젝트>/scripts/pipeline.py` 가 있으면 → **그 파일**을 사용.
2. 그 외(글로벌 scope, 또는 파일 없음) → **이 스킬 폴더의 `scripts/pipeline.py`(번들)** 를 절대 경로로 사용.
3. `.claude/harness.json` 자체가 없으면 `/harness:setup` 을 먼저 실행하라고 권한 뒤, 사용자가 원하면 번들 스크립트 + 기본값으로 그냥 진행해도 돼요.

스크립트는 **cwd 기준 git root** 에 phase 를 만들므로, 어느 복사본이든 실행 위치(cwd)가 곧 대상 레포예요.

## 0. 시작 전 질문 (필수)

`init` 하기 **전에 AskUserQuestion 으로 두 가지를 먼저** 물어요.

1. **worktree** — 이 phase 를 어디서 돌릴지
   - `전용 worktree` (기본, 병렬 안전): `.claude/worktrees/<slug>` 에 새 브랜치로 격리 → `init` 에 플래그 없음
   - `현재 체크아웃`: 지금 브랜치에서 바로 → `init --no-worktree`
2. **plan review** — 계획 검토를 어디까지 할지
   - `CEO + Eng 둘 다` (기본) → 플래그 없음
   - `CEO 만` / `Eng 만` → 둘 다 넣되(플래그 없음) 원치 않는 review stage 에서 실행 없이 `advance`
   - `생략` → `init --no-review`

답을 받은 뒤 그에 맞는 플래그로 init 해요. **compound 는 항상 빼니 `--no-compound` 를 늘 붙여요.**

## 1. phase 시작

phase 이름이 인자로 없으면 사용자에게 물어요. 그다음:

```bash
python3 <pipeline.py 경로> init "<phase 이름>" --no-compound [--no-worktree] [--no-review]
```

- 브랜치 이름은 입력한 이름(slug)을 대문자로 한 것 (예: "share fortune" → `SHARE-FORTUNE`). pipeline.py 가 알아서 만들어요.
- 전용 worktree 를 만들었으면 **이후 모든 명령은 그 worktree 안(cwd)에서** 실행해요:

```bash
cd .claude/worktrees/<slug>
```

## 2. stage 루프 (plan → make-pr)

`status` 로 지금 stage 를 확인하고, 그 stage 를 이 세션에서 실행한 뒤 `advance` 로 넘어가요. **make-pr 까지 반복.**

```bash
python3 <pipeline.py 경로> status
```

- **스킬 stage** (`/plan`, `/plan-ceo-review`, `/plan-eng-review`, `/ultrawork`, `/make-pr`)
  → 그 스킬을 실행하고, 결과가 만족스러우면 `advance`.
- **명령 stage** (`commit-push`)
  → 커밋 메시지는 Conventional Commits (`feat(<slug>): <뭐 했는지>`). git-master 위임 권장. 커밋·푸시 후 `advance`.
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

## 주의

- 전용 worktree 를 만든 경우, 모든 `status`/`advance` 는 그 worktree 안에서 실행해야 `phase.json` 을 찾아요.
- stage 가 실패하면 그 자리에서 멈추고, 고친 뒤 `status` 부터 다시.
- phase.json(`phases/<slug>/phase.json`)이 어느 stage 까지 왔는지 기억하므로, 중간에 끊겨도 이어서 진행할 수 있어요.
