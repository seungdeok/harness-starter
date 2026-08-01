---
title: "축적 레이어 — 규범(docs) vs 사실(.omc/wiki)"
tags: ["docs", "terminology", "adr", "compound"]
created: 2026-08-01T14:16:55.155Z
updated: 2026-08-01T14:16:55.155Z
sources: []
links: ["harness-plugin-scope-marketplace-sha.md", "omc-gitignore-layers.md", "pipeline-phase-slug-stage-worktree.md", "compound-engineering.md"]
category: convention
confidence: medium
schemaVersion: 1
---

# 축적 레이어 — 규범(docs) vs 사실(.omc/wiki)

이 레포는 지식을 **역할별로 다른 곳에** 쌓는다. 어디에 쓸지 헷갈릴 때 보는 표.

## 최상위 구분 (ADR-009)

| | `docs/` | `.omc/wiki/` |
| --- | --- | --- |
| 성격 | **규범** — 이렇게 하기로 했다 | **사실** — 이런 상태다 / 이렇게 동작한다 |
| 작성자 | 사람이 쓰고 PR 로 리뷰 | OMC 가 세션을 넘겨 축적 |
| 검토 | PR 리뷰를 거친다 | 안 거친다 |
| 커밋 | ✓ | ✓ (단, 자동 생성물은 제외 — 아래) |

핵심: **결정은 `docs/`, 관측은 `.omc/wiki/`.** "우리는 X 하기로 했다"는 ADR, "X 는 Y 로 동작한다"는 wiki.

## docs/ 안의 구분

| 파일 | 무엇을 적나 | 언제 쓰나 |
| --- | --- | --- |
| `PRD.md` | 무엇을 왜 만드는가 — 문제·목표·수용 기준 | 제품 범위가 정해질 때 |
| `ADR.md` | **결정과 그 대가**. 결정 / 이유 / 트레이드오프 / (후속) | 되돌리기 어려운 선택을 했을 때 |
| `ARCHITECTURE.md` | 시스템 구조·데이터 흐름·빌드법 | 구조가 바뀔 때 |
| `solutions/<slug>.md` | **한 사건의 해결 노트** — 문제 / 원인 / 해결 / 재발 방지 | 리뷰 후 compound 단계 |
| `solutions/GUARDRAILS.md` | 재발 방지 규칙 **한 줄씩** | 해결 노트가 일반화될 때 |
| `CHANGELOG.md` | **사용자가 체감하는** 변경 한 줄 | 스킬 동작·stage·설정 키가 바뀔 때 |

### ADR vs solutions vs GUARDRAILS — 가장 헷갈리는 셋
- **ADR**: "왜 이렇게 하기로 했나". 미래의 나를 설득하는 글. 검토했으나 **버린 안**과 그 이유가 핵심 자산.
- **solutions/\<slug\>.md**: "무엇을 잘못했고 어떻게 고쳤나". 사건 하나의 서사.
- **GUARDRAILS.md**: "다음부터 이렇게 한다". 한 줄 명령형 규칙. **다음 작업의 `plan`/`brainstorm` 이 먼저 읽는 grounding** 이라 실제로 행동을 바꾼다.

승격 방향은 한쪽이다: 사건 → 해결 노트 → (일반화되면) GUARDRAILS 한 줄.

### CHANGELOG 에 적는 것 / 안 적는 것 (CLAUDE.md §7)
- **적는다**: 스킬 동작, 파이프라인 stage, 설정 키 — `/plugin marketplace update` 를 돌린 사용자가 체감하는 것
- **안 적는다**: 내부 리팩터링, 오탈자, 문서 정리
- 헤딩은 `## <YYYY-MM-DD>` 날짜만. 항목 끝에 이슈/PR 번호. **버전 번호를 안 쓰는 이유**는 [[harness-plugin-scope-marketplace-sha]] 참고.

## .omc/wiki/ 안의 구분 — 큐레이션 vs 자동 생성

`.omc/wiki/` 안이라고 다 "사실"은 아니다. OMC 가 세션마다 만드는 부산물이 섞인다.

| 파일 | 성격 | 커밋 |
| --- | --- | --- |
| 큐레이션 페이지 (이 문서 같은) | 사람/에이전트가 의도해서 쓴 사실 | ✓ |
| `index.md` | 자동 재생성 카탈로그. `CLAUDE.md` 가 `@` 로 임포트 | ✓ |
| `session-log-<date>-<id>.md` | 세션 ID + 보일러플레이트. 정보량 0 | ✗ |
| `log.md` | ingest 감사 로그, append-only | ✗ |
| `environment.md` | 자동 감지 산출물 | ✗ |

제외는 `.omc/.gitignore` 가 담당한다. 상세는 [[omc-gitignore-layers]].

## 관련
[[pipeline-phase-slug-stage-worktree]] · [[compound-engineering]] · [[omc-gitignore-layers]]

