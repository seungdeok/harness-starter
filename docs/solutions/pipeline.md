# Harness Pipeline — plan → … → compound 루프

한 작업(phase)을 `plan → plan-review → implement → commit&push → make-pr → compound`
순서로 돌리고, 끝나면 새 phase 를 수동으로 시작하는 반자동 루프예요.
어느 stage 까지 왔는지는 `phases/<slug>/phase.json` 이 기억해요.
`pipeline.py` 자체는 **의존성 0(stdlib)** 짜리 stage 체커예요.

## Stage 매핑

OMC/내부 스킬 우선. compound 만 CLAUDE.md 5장이 `/ce-compound` 를 지정.

| stage           | action                                 | 하는 일                                        |
| --------------- | -------------------------------------- | ---------------------------------------------- |
| plan            | `/plan` (OMC)                          | 요구사항 → 실행 계획                           |
| plan-review-ceo | `/plan-ceo-review`                     | 계획을 CEO 렌즈로 검토                         |
| plan-review-eng | `/plan-eng-review`                     | 계획을 엔지니어 렌즈로 검토                    |
| implement       | `/ultrawork` (OMC)                     | 계획대로 구현                                  |
| commit-push     | `git add -A && git commit && git push` | 커밋(=lefthook 이 lint 실행) + 푸시            |
| make-pr         | `/make-pr`                             | 현재 브랜치로 draft PR                         |
| compound        | `/ce-compound`                         | 교훈을 `docs/solutions/` 에 기록 (CLAUDE.md 5장) |

> **plan review 선택** — `init` 이 한 번 물어봐서(`[Y/n]`) plan-review(ceo/eng) 두 stage 를
> 넣거나 뺄 수 있어요. 안 물어보고 바로 생략하려면 `init "<name>" --no-review`. 비대화형에선 기본 포함.

> **implement 선택지** — `/ultrawork` 는 계획 받아 바로 구현(선작업 0). step 단위까지 자동화하고
> 싶으면 `phases/<slug>/step*.md` + `index.json` 을 쓰고 action 을 `execute.py <slug>` 로 교체하세요.
> execute.py 는 의존성이 없지만 step 을 미리 쪼개는 선작업이 늘어요.

## Phase 당 worktree (init 이 자동 생성)

`init` 이 phase 마다 **전용 worktree**(`.claude/worktrees/<slug>`, 브랜치 `feat-<slug>`)를
만들고 그 안에 `phases/<slug>/phase.json` 을 심어요. 메인 체크아웃 브랜치는 건드리지
않으므로, **worktree 를 여러 개 띄우면 phase 를 병렬로** 돌릴 수 있어요.
`init` 이후의 `status`/`advance`/`run` 은 해당 worktree 안에서 실행하세요.
phase 가 끝나(PR 머지) 정리할 땐 `git worktree remove .claude/worktrees/<slug>`.

## 대화형 흐름 (기본)

각 stage 를 **이 세션에서 스킬로 직접 실행**하고, 통과하면 `advance` 로 넘어가요.

```bash
# 1. phase 시작 (.claude/worktrees/share-fortune worktree + feat-share-fortune 브랜치 생성)
python3 scripts/pipeline.py init "share fortune"
cd .claude/worktrees/share-fortune         # 이후 명령은 worktree 안에서

# 2. 지금 실행할 stage 확인
python3 scripts/pipeline.py status
#   ▶ [1/7] plan — 스킬: /plan

# 3. 그 스킬을 세션에서 실행 → 결과가 만족스러우면 넘어가기
#    (세션에서 /plan 실행)
python3 scripts/pipeline.py advance --summary "공유 기능 계획 확정"

# 4. status → advance 를 7번 반복. commit-push 는 스킬 대신 명령이라 직접 실행:
git add -A && git commit && git push -u origin HEAD && python3 scripts/pipeline.py advance

# 5. compound 까지 advance 하면 phase 완료. 다음 작업은 다시 init 부터.
```

`status`/`advance` 는 진행 중 phase 가 하나면 인자 없이 자동으로 찾아요.
여러 개면 `advance share-fortune` 처럼 이름을 줘요.

## Headless 흐름 (옵션)

스킬 stage 를 `claude -p` 로 자동 실행해요. **사람이 검토하지 않으니** 계획이 흔들려도 진행돼요.
그리고 `run` 은 **명령 stage(commit-push)를 만나면 멈춰요** — 커밋 메시지·판단이 필요하니까요.
그래서 권장 사용은:

- **plan / 리뷰 는 대화형으로** 확정한 뒤(= cursor 가 implement 로 이동),
- implement 만 자동으로 굴리고, commit-push 부터는 다시 대화형:

```bash
python3 scripts/pipeline.py init "share fortune"
# 세션에서 /plan, /plan-ceo-review, /plan-eng-review 실행 후 advance 세 번…
python3 scripts/pipeline.py run     # implement 자동 실행 → commit-push 앞에서 멈춤
```

`run` 은 스킬 stage 마다 `phases/<slug>/stage-<name>-output.json`(gitignore 됨) 에 로그를 남기고,
실패하거나 명령 stage 를 만나면 멈춰서, 사람이 처리 후 다시 `run`/`advance` 하면 이어서 진행해요.

## phase.json

```json
{ "phase": "share-fortune", "branch": "feat-share-fortune", "cursor": 2,
  "stages": [
    {"name":"plan","action":"/ce-plan","status":"completed","summary":"…"},
    {"name":"plan-review","action":"/ce-doc-review","status":"completed"},
    {"name":"implement","action":"/ce-work","status":"pending"}, … ] }
```

`cursor` 가 현재 stage 인덱스예요. 커밋해서 팀과 공유해도 되고, 로컬 상태로만 둬도 돼요
(stage 출력 `stage-*-output.json` 만 gitignore).

## 로직 검증

```bash
python3 scripts/pipeline.py selftest   # cursor/advance/slug 순수 로직 체크
```
