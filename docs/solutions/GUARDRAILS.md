# GUARDRAILS — 재발 방지 규칙

실행-검토에서 나온 교훈 중 "다음부터 이렇게 하면 그 실수를 안 한다" 수준으로 일반화된 규칙만 한 줄씩 모아요.
compound 단계에서 새 규칙이 생기면 여기에 추가하고, 다음 작업의 `plan`/`brainstorm`이 이 목록을 먼저 읽어요.
개별 사례의 자세한 맥락은 `docs/solutions/<slug>.md` 해결 노트에 있어요.

## 규칙

- [2026-08-01] CI 체크를 추가하면 일부러 깨뜨려 `exit 1` 이 나오는지 확인한다 — 통과만 본 체크는 실제로 막는지 알 수 없다. (근거: ci-check-coverage.md)
- [2026-08-01] 검사 도구가 덮는 파일이 `git log` 상 실제로 자주 바뀌는 파일과 겹치는지 대조한다 — 안 바뀌는 파일만 덮으면 안전망이 아니다. (근거: ci-check-coverage.md)
- [2026-08-01] `gh issue view`/`gh pr edit` 가 Projects classic GraphQL 에러를 내면 `gh api` 로 우회한다. (근거: ci-check-coverage.md)
- [2026-08-01] harness 가 대상 레포에 뿌리는 것(gitignore 줄·훅·스크립트·CI)은 대상 레포에 런타임 의존을 만들지 않는다 — 대상의 언어·툴체인을 모르는 게 기본값이다. (근거: plugin-target-repo-no-dependency.md)
- [2026-08-01] 근거를 대서 배제한 안을 다시 선택지에 올릴 때는 그 근거가 선호 문제인지 제약인지 구분한다 — 제약이면 옵션에서 뺀다. 단점을 설명에 적어두는 건 제약을 선호로 격하시키는 것이다. (근거: plugin-target-repo-no-dependency.md)
- [2026-08-01] 루트 `CLAUDE.md` 를 고치면 `skills/setup/templates/CLAUDE-section.md` 미러도 같이 고친다 — 대상 레포에만 규범이 빠지면 원래 버그보다 나쁘다. (근거: plugin-target-repo-no-dependency.md)
- [2026-08-01] 스킬·문서에 써 넣는 셸 명령은 "결과 있음"과 "결과 없음" 두 상태로 실제 실행해 본다 — 결함은 대개 없음 쪽에 숨어 있다. (근거: skill-prose-commands.md)
- [2026-08-01] 매칭이 없을 수 있는 조회에는 `ls *.ext` 대신 `find <dir> -name '*.ext'` 를 쓴다 — zsh 의 glob nomatch 에러는 `2>/dev/null` 로 안 막힌다. (근거: skill-prose-commands.md)
- [2026-08-01] CLI 플래그는 `--help` 로 설치된 버전에 실제 있는지 확인한다 — 공식 문서에 있어도 구버전엔 없다. (근거: skill-prose-commands.md)
- [2026-08-01] 문서가 "레포의 X 형식에 맞춰"라고 서술하면 X 를 읽는 단계가 절차에 실제로 있는지 대조한다 — plugin 은 남의 레포에서 도니 "우리 레포에서 잘 됨"은 검증이 아니다. (근거: skill-prose-commands.md)
- [2026-08-01] worktree phase 의 `pipeline.py status`/`advance` 는 매번 `cd <worktree> && ...` 한 줄로 실행한다 — 앞 명령의 셸 cwd 에 기대면 활성 phase 가 하나뿐인 다른 레포에서 조용히 엉뚱한 phase 가 advance 된다. (근거: pipeline-worktree-cwd.md)
- [2026-08-01] 에이전트가 컨텍스트로 이미 갖고 있는 정보(가용 스킬 목록 등)는 코드로 재구현하지 않는다 — 캐시 경로·설치 상태에 종속된 탐지는 드리프트한다. (근거: ADR-007)
- [2026-08-01] 외부 도구(git·CLI·SDK)의 실패 조건에 설계가 걸려 있으면 plan 전에 임시 리소스로 한 번 돌려본다 — 문서에 없는 거부 조건이 정상 경로를 통째로 막을 수 있다. (근거: probe-constraints-before-planning.md)
- [2026-08-01] probe·임시 산출물을 지울 때는 만든 것만 지운다 — 부모 디렉토리 `rmtree`/`rm -rf` 는 그 안의 추적 파일까지 가져간다. 지운 뒤 `git status` 로 예상 밖 삭제를 확인한다. (근거: probe-constraints-before-planning.md)
