# Harness Pipeline — discuss → … → make-pr 루프

한 작업(phase)을 `discuss → plan → [plan-review-ceo] → [plan-review-eng] → approve →
implement-red → implement-green (TDD, 기본) | implement (--no-tdd) → verify →
commit-push → make-pr` 순서로 돌리고, 끝나면 새 phase 를 수동으로 시작하는 반자동 루프예요.
어느 stage 까지 왔는지는 `phases/<slug>/phase.json` 이 기억해요.
`pipeline.py` 자체는 **의존성 0(stdlib)** 짜리 stage 체커예요.

> **스크립트 위치** — plugin 번들(`skills/pipeline/scripts/pipeline.py`)이 단일 소스예요.
> `/harness:setup` 을 프로젝트 scope 로 돌리면 `<프로젝트>/scripts/pipeline.py` 로 복사돼요.
> 아래 예시의 `<pipeline.py>` 는 그 둘 중 하나의 경로예요. 스크립트는 **cwd 기준 git root** 에
> phase 를 만들므로(스크립트 위치와 무관), worktree 안에서 실행하면 그 worktree 가 대상이에요.

## Stage 매핑

OMC/내부 스킬 우선. discuss/approve 는 스킬 없이 이 세션에서 사람이 직접 진행하는 대화형 stage.
compound 만 CLAUDE.md 5장이 `/ce-compound` 를 지정.

| stage            | action                                  | 하는 일                                          |
| ---------------- | ---------------------------------------- | ------------------------------------------------ |
| discuss          | (대화형, 스킬 없음)                      | 자유 대화로 요구사항 정리                        |
| plan             | `/plan` (OMC)                            | 요구사항 → 실행 계획 (`phases/<slug>/plan.md`)   |
| plan-review-ceo  | `/plan-ceo-review`                       | 계획을 CEO 렌즈로 검토                           |
| plan-review-eng  | `/plan-eng-review`                       | 계획을 엔지니어 렌즈로 검토                      |
| approve          | (대화형, 스킬 없음)                      | `plan.md` 승인 — 거절 시 제자리 수정 후 재승인   |
| implement-red    | `/ultrawork` (OMC, TDD)                  | 실패하는 테스트만 작성, 올바른 이유로 실패 확인  |
| implement-green  | `/ultrawork` (OMC, TDD)                  | 최소 구현으로 테스트 통과 (red 테스트 수정 금지) |
| verify           | `/verify` (OMC)                          | `plan.md` 수용 기준·실제 동작을 증거로 검증      |
| commit-push      | 범위 확인 → `git add <파일> && commit && push` | 커밋 범위를 먼저 확인받고(`git add -A` 금지) 푸시 |
| make-pr          | `/make-pr`                               | 현재 브랜치로 draft PR                           |
| compound         | `/ce-compound`                           | 교훈을 `docs/solutions/` 에 기록 (CLAUDE.md 5장) |

> **plan review 선택** — `init` 이 한 번 물어봐서(`[Y/n]`) plan-review(ceo/eng) 두 stage 를
> 넣거나 뺄 수 있어요. 안 물어보고 바로 생략하려면 `init "<name>" --no-review`. 비대화형에선 기본 포함.

> **TDD 선택** — `implement-red`/`implement-green` 이 기본이에요. `init "<name>" --no-tdd` 를 주면
> 둘 대신 `implement`(`/ultrawork`) 단일 stage 로 돌아가요.

> **compound** — 파이프라인은 `--no-compound` 를 늘 붙여 기본 제외해요. 필요하면 종료 후 `/ce-compound` 를 직접 실행.

> **implement 선택지** — `/ultrawork` 는 계획 받아 바로 구현(선작업 0). step 단위까지 자동화하고
> 싶으면 `phases/<slug>/step*.md` + `index.json` 을 쓰고 action 을 `execute.py <slug>` 로 교체하세요.
> execute.py 는 의존성이 없지만 step 을 미리 쪼개는 선작업이 늘어요.

## Phase 당 worktree (init 이 자동 생성)

`init` 이 phase 마다 **전용 worktree**(`.claude/worktrees/<slug>`, 브랜치는 입력 이름을
대문자로 한 `<SLUG>`)를 만들고 그 안에 `phases/<slug>/phase.json` 을 심어요. 메인 체크아웃 브랜치는 건드리지
않으므로, **worktree 를 여러 개 띄우면 phase 를 병렬로** 돌릴 수 있어요.
`init` 이후의 `status`/`advance`/`run` 은 해당 worktree 안에서 실행하세요.
phase 가 끝나(PR 머지) 정리할 땐 `git worktree remove .claude/worktrees/<slug>`.

## 대화형 흐름 (기본)

각 stage 를 **이 세션에서 스킬로 직접 실행**하고, 통과하면 `advance` 로 넘어가요.

```bash
# 1. phase 시작 (.claude/worktrees/share-fortune worktree + SHARE-FORTUNE 브랜치 생성)
python3 <pipeline.py> init "share fortune"
cd .claude/worktrees/share-fortune         # 이후 명령은 worktree 안에서

# 2. 지금 실행할 stage 확인
python3 <pipeline.py> status
#   ▶ [1/11] discuss — 대화형: 이슈·요구사항을 사용자와 자유 대화로 논의

# 3. 그 stage 를 세션에서 진행 → 결과가 만족스러우면 넘어가기
#    (discuss/approve 는 대화로, 나머지는 해당 스킬 실행)
python3 <pipeline.py> advance --summary "공유 기능 요구사항 합의"

# 4. status → advance 를 stage 수만큼 반복. commit-push 는 스킬 대신 명령이라 직접 실행:
#    (phases/ 가 untracked 로 뜨니 `git add -A` 금지 — 커밋할 파일을 명시. CLAUDE.md §6)
git add <변경 파일…> && git commit && git push -u origin HEAD && python3 <pipeline.py> advance

# 5. 마지막 stage 까지 advance 하면 phase 완료. 다음 작업은 다시 init 부터.
```

`status`/`advance` 는 진행 중 phase 가 하나면 인자 없이 자동으로 찾아요.
여러 개면 `advance share-fortune` 처럼 이름을 줘요.

## Headless 흐름 (resume 전용 헬퍼)

`run` 은 스킬 stage 를 `claude -p` 로 자동 실행하는 **resume 전용 헬퍼**예요. 새 phase 는
첫 stage 인 discuss(대화형)에서 바로 멈추므로 "끝까지 전자동"은 없어요 (ADR-004).
`run` 이 멈추는 곳:

- **discuss / approve** — 대화형 stage, 사람과의 대화가 곧 실행이라 headless 불가
- **implement-red 완료 직후** — 테스트가 올바른 이유로 실패하는지 사람이 확인
- **commit-push** — 커밋 메시지·판단이 필요한 명령 stage
- 스킬 stage 실패 시

권장 사용: **approve 까지 대화형으로 확정**한 뒤, implement 구간만 자동으로 굴려요:

```bash
# 세션에서 discuss…approve 까지 advance 한 상태에서
python3 <pipeline.py> run   # red 실행 → 멈춤(실패 확인) → 다시 run → green·verify → commit-push 앞에서 멈춤
```

`run` 은 스킬 stage 마다 `phases/<slug>/stage-<name>-output.json` 에 로그를 남기고,
멈춘 자리에서 사람이 처리 후 다시 `run`/`advance` 하면 이어서 진행해요.

## phase.json

```json
{ "phase": "share-fortune", "branch": "SHARE-FORTUNE", "cursor": 2,
  "stages": [
    {"name":"discuss","action":"이슈·요구사항을 사용자와 자유 대화로 논의","status":"completed","summary":"…"},
    {"name":"plan","action":"/plan","status":"completed"},
    {"name":"plan-review-ceo","action":"/plan-ceo-review","status":"pending"}, … ] }
```

`cursor` 가 현재 stage 인덱스예요. red/green record 는 `hint` 필드(TDD 지시문)를 추가로 가져요.
`phases/` 아래는 `plan.md` 까지 전부 커밋하지 않아요. gitignore 규칙도 두지 않아서 `git status` 에
untracked 로 뜨는 게 정상이에요 (ADR-005, CLAUDE.md §6).

## 로직 검증

```bash
python3 <pipeline.py> selftest   # cursor/advance/slug 순수 로직 체크
```
