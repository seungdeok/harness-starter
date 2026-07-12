# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

## 5. Compound — 작업의 마지막 단계 (리뷰 후 필수)

**모든 단위 작업은 다음 작업을 더 쉽게 만들어야 한다. 리뷰가 끝나면 그냥 끝내지 말고, 이번에 겪은 실수·교훈을 프로세스에 남긴다.**

Compound Engineering 루프: `brainstorm → plan → work → simplify → review → compound`.
각 단계에서 쓰는 스킬: **simplify → `/simplify`** (변경 diff에 재사용·단순화·효율 정리 적용, 버그 탐색 아님) → **review → `/ce-code-review` 또는 `/code-review`** (변경 diff의 버그·정리 지적). (`/review`는 GitHub PR 전용이라 이 로컬 루프에서는 쓰지 않는다.)
코드 변경이 포함된 작업이 **리뷰(`/ce-code-review` 또는 일반 코드 리뷰)까지 끝나면**, 아래 compound 단계를 반드시 수행한다. (사소한 질의·조회·문서 오탈자 같은 무변경 작업은 제외)

1. **회고**: 이번 실행–검토 과정에서 발생한 실수, 헛디딤, 되풀이하기 싫은 판단 미스, 새로 배운 것을 1~3줄로 정리한다.
2. **기록**: `/ce-compound`로 `docs/solutions/<slug>.md`에 해결 노트를 남긴다 — _문제 / 원인 / 해결 / 재발 방지_. 다음 에이전트가 같은 교훈을 처음부터 다시 배우지 않게 한다.
3. **승격**: 재발 방지 규칙이라면 `docs/solutions/GUARDRAILS.md`에 한 줄 규칙으로 올린다. 이 파일은 다음 작업의 `plan`/`brainstorm`이 먼저 읽는 grounding이 되어, 같은 실수를 구조적으로 막는다.

배운 게 없으면 "특이사항 없음"이라고만 남기고 넘어간다. 핵심은 **리뷰에서 끝내지 않고, 교훈을 다음 사이클로 되먹이는 것**이다.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

## Project Docs

@docs/PRD.md
@docs/ADR.md
@docs/ARCHITECTURE.md
@docs/solutions/GUARDRAILS.md
