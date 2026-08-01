---
title: "Compound Engineering 루프와 스킬 매핑"
tags: ["compound", "terminology", "skills", "review"]
created: 2026-08-01T14:17:50.593Z
updated: 2026-08-01T14:17:50.593Z
sources: []
links: ["docs-vs-omc-wiki.md", "pipeline-phase-slug-stage-worktree.md"]
category: convention
confidence: medium
schemaVersion: 1
---

# Compound Engineering 루프와 스킬 매핑

CLAUDE.md §5 가 정의하는 루프와, 각 단계에 실제로 쓰는 스킬.

## 루프

```
brainstorm → plan → work → simplify → review → compound
```

| 단계 | 스킬 | 하는 일 |
| --- | --- | --- |
| brainstorm | `/ce-brainstorm` | 막연한 아이디어를 요구사항으로 |
| plan | `/ce-plan` 또는 `/plan` | 실행 계획 |
| work | `/ce-work`, `/ultrawork` | 구현 |
| **simplify** | **`/simplify`** | 변경 diff 에 재사용·단순화·효율 정리 적용. **버그 탐색이 아님** |
| **review** | **`/ce-code-review`** 또는 **`/code-review`** | 변경 diff 의 **버그·정리 지적** |
| compound | `/ce-compound` | 교훈을 `docs/solutions/<slug>.md` 에 기록 |

## 헷갈리는 리뷰 스킬 4종

| 스킬 | 대상 | 무엇을 보나 |
| --- | --- | --- |
| `/simplify` | 로컬 변경 diff | 재사용·단순화·효율 (**버그 아님**) |
| `/ce-code-review` | 로컬 변경 diff | 버그·회귀·테스트·표준 |
| `/code-review` | 로컬 변경 diff | 버그 |
| `/review` | **GitHub PR 전용** | — |

**`/review` 는 이 로컬 루프에서 쓰지 않는다.** GitHub PR 전용이라 로컬 브랜치 작업에는 맞지 않는다. (CLAUDE.md §5 가 명시)

simplify 와 review 를 **분리된 패스**로 두는 이유: 저자 패스와 검토 패스를 같은 컨텍스트에서 겸하면 자기 승인이 된다. 승인 패스는 별도 레인(`code-reviewer`/`verifier`)에서 돈다.

## compound 는 언제 필수인가

**코드 변경이 포함된 작업이 리뷰까지 끝나면 필수.** 사소한 질의·조회·문서 오탈자 같은 무변경 작업은 제외.

3단계로 진행한다:
1. **회고** — 이번 실행–검토에서 나온 실수·헛디딤·새로 배운 것을 1~3줄로
2. **기록** — `/ce-compound` 로 `docs/solutions/<slug>.md` (문제 / 원인 / 해결 / 재발 방지)
3. **승격** — 일반화된 재발 방지 규칙이면 `docs/solutions/GUARDRAILS.md` 에 한 줄

배운 게 없으면 "특이사항 없음"만 남기고 넘어간다.

## compound 는 파이프라인 stage 가 아니다

`/harness:pipeline` 은 **항상 `--no-compound`** 로 돈다 (ADR-001). 사람이 회고를 판단해야 하는 단계라 자동화 stage 로 묶으면 형식적 기록만 남기 때문.

그래서 빼먹기 쉬웠고, ADR-009 가 **`pipeline.py done` 에 게이트**를 넣어 실제로 막는다:

> 브랜치가 `<docs>/solutions/` 를 하나도 안 건드렸으면 **아무것도 지우지 않고 거부**한다.
> 우회는 `done <slug> --force`. origin 이 없어 base 를 못 찾으면 차단 대신 경고.

이 게이트는 "`docs/solutions/` 를 건드렸는가"라는 **대리 지표**라 빈 파일을 만들어도 통과한다. 형식적 통과를 막는 건 사람의 몫이고, 게이트의 목적은 **증류를 잊는 것**을 막는 데 있다.

## 규범을 도구가 아니라 문서로 강제하는 선례

이 레포는 반복해서 "훅/CI 로 막기"보다 "CLAUDE.md 규범 + PR 리뷰"를 택했다 — ADR-005(`phases/` 커밋 금지), ADR-007(하드 의존 스킬 점검), ADR-010(수동 CHANGELOG). 이유는 대상 레포에 런타임 의존을 만들지 않기 위해서이고, 대가는 "빼먹으면 그냥 구멍"이라는 **인정된 비용**이다.

예외적으로 `done` 의 compound 게이트만 코드로 강제한다 — worktree 가 사라지면 그 작업이 아무것도 남기지 못하는, 되돌릴 수 없는 손실이라서.

## 관련
[[docs-vs-omc-wiki]] · [[pipeline-phase-slug-stage-worktree]]

