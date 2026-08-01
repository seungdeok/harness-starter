# GUARDRAILS — 재발 방지 규칙

실행-검토에서 나온 교훈 중 "다음부터 이렇게 하면 그 실수를 안 한다" 수준으로 일반화된 규칙만 한 줄씩 모아요.
compound 단계에서 새 규칙이 생기면 여기에 추가하고, 다음 작업의 `plan`/`brainstorm`이 이 목록을 먼저 읽어요.
개별 사례의 자세한 맥락은 `docs/solutions/<slug>.md` 해결 노트에 있어요.

## 규칙

- [2026-08-01] CI 체크를 추가하면 일부러 깨뜨려 `exit 1` 이 나오는지 확인한다 — 통과만 본 체크는 실제로 막는지 알 수 없다. (근거: ci-check-coverage.md)
- [2026-08-01] 검사 도구가 덮는 파일이 `git log` 상 실제로 자주 바뀌는 파일과 겹치는지 대조한다 — 안 바뀌는 파일만 덮으면 안전망이 아니다. (근거: ci-check-coverage.md)
- [2026-08-01] `gh issue view`/`gh pr edit` 가 Projects classic GraphQL 에러를 내면 `gh api` 로 우회한다. (근거: ci-check-coverage.md)
