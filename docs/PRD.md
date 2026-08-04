# PRD — harness

Claude Code 에이전트 한 명이 **작업 하나(phase)** 를 요구사항 정리부터 draft PR 까지,
승인 게이트를 건너뛰지 않고 끝내게 하는 파이프라인 하네스. Claude Code plugin 으로 배포한다.

> 이 문서는 **지금까지 무엇을 왜 만들었는지**(§6 완료분)와 **다음에 무엇을 증명할 건지**(§6 다음
> 마일스톤)를 함께 적는다. 개별 결정의 근거는 [`ADR.md`](ADR.md), 동작 구조는
> [`ARCHITECTURE.md`](ARCHITECTURE.md) 에 있다.

## 1. 문제

에이전트에게 작업을 맡기면 세 가지가 반복해서 무너진다.

1. **계획 승인 없이 코드가 먼저 나온다.** 방향이 틀린 걸 diff 를 보고서야 안다.
2. **검증이 "돌려봤다" 수준에서 끝난다.** 정방향 통과만 보고, 그 실행이 대상 코드 경로를
   실제로 밟았는지는 아무도 안 본다.
3. **이번에 배운 것이 다음 세션에 남지 않는다.** 셋 중 가장 비싸다 — 같은 실수를 매번 처음부터
   다시 배우고, 그 비용은 세션 수에 비례해 늘어난다.

## 2. 목표 (MVP)

- phase 하나가 **세션이 끊겨도 상태를 잃지 않고** 끝까지 간다.
- 사람이 서야 하는 자리(계획 승인·커밋 범위)를 **생략할 수 없다.**
- 작업이 끝나면 교훈이 **레포에 남고, 그게 다음 작업의 입력이 된다.**

"기능이 다 붙었다"가 아니라 §6 의 검증 가능한 조건으로 판정한다.

## 3. 대상 사용자

Claude Code 를 쓰는 개발자 — **공개 배포**를 전제로 한다. 설치자는 이 레포를 모르는 사람이고,
자기 레포에서 `/plugin install` 후 바로 써야 한다.

전제: `oh-my-claudecode`(OMC) 가 깔려 있어야 한다 — `/plan`·`/ultrawork`·`/verify` 는 대안이 없는
하드 의존이다([ADR-004](ADR.md#adr-004)). gstack plan review·compound-engineering·`gh` 는 선택이고,
없으면 해당 경로를 닫고 안내한다.

## 4. 범위 (MVP)

plugin 에 담기는 스킬 4개: `pipeline`·`setup`·`make-pr`·`make-issue`.
그리고 의존성 0(stdlib)짜리 stage 체커 `pipeline.py`.

## 5. 기능 요구사항

| ID  | 요구사항 | 근거 |
| --- | --- | --- |
| FR1 | phase 를 `init` 으로 만들고 `status`/`advance` 로 stage 를 하나씩 진행한다. 진행 상태는 `phases/<slug>/phase.json` 에 남아 세션이 끊겨도 이어서 간다 | [ARCHITECTURE](ARCHITECTURE.md) |
| FR2 | `init` 이 phase 마다 전용 worktree(`.claude/worktrees/<slug>`)와 대문자 브랜치(`<SLUG>`)를 만든다 — phase 를 병렬로 돌릴 수 있다 | [ADR-001](ADR.md#adr-001) |
| FR3 | `discuss`·`approve`·커밋 범위 확인은 **opt-out 이 없는** human gate 다 | [ADR-004](ADR.md#adr-004) |
| FR4 | TDD 가 기본이다 — `implement` 자리에 `implement-red`/`implement-green` 을 splice 하고, red 직후 사람이 실패 이유를 확인한다 (`--no-tdd` 로 해제) | [ADR-004](ADR.md#adr-004) |
| FR5 | `/harness:setup` 이 scope·docs 경로를 묻고 초기화한다. **기존 파일을 덮어쓰지 않는다** — `CLAUDE.md` 는 마커 사이 append 만 하고, 재실행 시 사전 스캔으로 확인을 한 번만 받는다 | [ADR-002](ADR.md#adr-002)·[013](ADR.md#adr-013) |
| FR6 | 프로젝트 scope 로 복사한 `pipeline.py` 는 출처 SHA 헤더를 달고, 출처를 모르면 **복사하지 않는다** | [ADR-008](ADR.md#adr-008) |
| FR7 | `make-pr`·`make-issue` 는 대상 레포의 템플릿을 읽어 그 구조로 쓰고, 없을 때만 내장 형식으로 fallback 한다 | [ADR-006](ADR.md#adr-006) |
| FR8 | 파이프라인은 `init` **이전에** 하드 의존 스킬 가용성을 점검한다 — worktree·브랜치를 만들기 전이라야 손해가 0이다 | [ADR-007](ADR.md#adr-007) |
| FR9 | `done` 은 worktree 를 지우기 전에 이 작업의 교훈이 `origin/<base>` 에 **도착**했는지 확인하고, 아니면 아무것도 지우지 않는다 | [ADR-012](ADR.md#adr-012) |
| FR10 | 사용자가 체감하는 변경은 `CHANGELOG.md` 에 남는다 — `plugin.json` 에 `version` 이 없어 커밋 SHA 가 곧 버전이기 때문 | [ADR-010](ADR.md#adr-010) |

## 6. 성공 지표 (Acceptance)

**완료** — 이 레포 안에서 실증됨:

- [x] phase 하나를 `discuss` → `make-pr` 까지 stage 상태를 잃지 않고 완주한다 (issue #7 이후 실사용)
- [x] 승인(`approve`) 없이 구현 stage 로 넘어갈 수 없다
- [x] `setup` 재실행이 기존 파일을 덮어쓰지 않고, 무엇을 왜 스킵했는지 파일 단위로 출력한다
- [x] `done` 이 교훈 미도착 시 **아무것도 지우지 않고** 거부한다 (임시 레포 3케이스 실증)
- [x] 지식이 `docs/` 한 곳에만 쌓이고, ADR·해결 노트·GUARDRAILS 가 서로 링크된다

**다음 마일스톤** — 아직 증명 못 한 것. 셋 다 "만들었다"가 아니라 "쓰였다"를 묻는다:

- [ ] **남의 레포에서 실제로 돈다** — 이 레포가 아닌 레포 1건에서 `/harness:setup` → phase 1개
      종단 완주. 지금까지 모든 검증은 이 레포 안에서만 했고, harness 는 plugin 이므로 그건 검증이 아니다.
- [ ] **문서가 근거로 쓰인다** — `plan`/`brainstorm` 산출물이 `GUARDRAILS.md` 의 규칙을 인용해
      선택지를 바꾼 사례 3건. 인용이 없으면 규칙 35줄은 비용만 남는다.
- [ ] **compound 가 다음 작업을 바꾼다** — 이전 교훈 덕분에 하지 않은 일이 노트에 기록된 사례 1건
      ("이 규칙이 있어서 X 를 검토 대상에서 뺐다"). 규칙이 쌓이는 것과 규칙이 쓰이는 것은 다르다.

## 7. Non-Goals (제외)

- **멀티 에이전트 오케스트레이션.** phase 하나 = 브랜치 하나 = 세션 하나가 단위다. 병렬은
  worktree 를 여러 개 띄우는 것으로 하고, 에이전트를 지휘하지 않는다.
- **끝까지 전자동.** `run` 은 resume 전용 헬퍼다. 승인 게이트가 목적이므로 전자동은 목표가 아니다
  ([ADR-004](ADR.md#adr-004)).
- **`phases/` 산출물 커밋.** `plan.md` 도 포함해 전부 로컬 산출물이다 ([ADR-005](ADR.md#adr-005)).
- **`plugin.json` 의 `version` 필드.** 넣으면 캐시 경로가 바뀌어 project scope 복사가 거부된다
  ([ADR-010](ADR.md#adr-010)).
- **`.yml` Issue Forms 파싱.** 구조 변환이 필요해 fallback 으로 보낸다 ([ADR-006](ADR.md#adr-006)).
- **대상 레포에 런타임 의존 추가.** 훅·CI·린터를 뿌리지 않는다 (§철학, [ADR-005](ADR.md#adr-005)).
