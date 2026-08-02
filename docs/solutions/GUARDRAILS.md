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
- [2026-08-01] PR 범위는 `git diff origin/<base>...HEAD` (세 점, fetch 후)로 본다 — `git diff A..B` 는 두 tip 비교라 그 사이 전진한 남의 커밋이 내 diff 로 섞여 보이고, 로컬 `main` 은 worktree 작업 중 며칠씩 안 움직인다. (근거: pr-scope-two-dot-diff.md)
- [2026-08-01] 커밋 전에 `git merge-tree --write-tree origin/<base> HEAD` 로 충돌을 미리 본다 — 작업트리를 안 건드리고 exit code 만 준다. 머지 불가 브랜치를 push 한 뒤 PR 단계에서 아는 건 늦다. (근거: pr-scope-two-dot-diff.md)
- [2026-08-01] 설계 문서를 실행 단위로 삼기 전에 "현재 상태" 절을 레포로 대조한다 — 문서는 시점이 고정되고 코드는 안 그렇다. 이번엔 작업 9개 중 7개가 이미 끝났거나 이미 거부된 안이었다. (근거: spec-baseline-drift.md)
- [2026-08-01] 문서가 "이미 강제된다/완화됨"이라고 적은 칸을 "미검증" 칸보다 먼저 검증한다 — 미검증은 이미 의심받고 있어서 안전하고, 아무도 다시 안 보는 확인됨 칸이 구멍을 가린다. (근거: spec-baseline-drift.md)
- [2026-08-01] 남의 도구 상태 디렉토리(`.omc/` 등)에 산출물을 두기 전에 그 도구가 그 경로를 쓰는지 소스로 확인한다 — 이름이 비어 보이는 것과 비어 있는 것은 다르다. (근거: spec-baseline-drift.md)
- [2026-08-01] `.gitignore` 를 고치면 `git check-ignore -v` 로 무시될 것과 추적될 것을 모두 찍는다 — 패턴에 슬래시가 없으면 모든 깊이를 매칭하고, 중첩 `.gitignore` 가 루트를 이기며, 도구가 자기 규칙을 매 실행 되돌릴 수 있다. 셋 다 조용히 실패한다. (근거: spec-baseline-drift.md)
- [2026-08-01] 정방향 통과를 근거로 삼기 전에 그 실행이 대상 코드 경로를 실제로 밟는지 역방향으로 확인한다 — 조건을 뒤집어도 결과가 그대로면 통과한 게 아니라 아무것도 안 돈 것이다. 읽기 툴은 대개 mutation boundary 를 우회한다. (근거: verification-trigger-coverage.md)
- [2026-08-01] 도구가 생성한 파일을 손으로 고치면 본문에서 파생된 메타데이터(frontmatter `links`·인덱스)도 함께 재생성한다 — 검사 도구는 본문이 아니라 그 필드를 읽는다. (근거: omc-wiki-page-authoring.md)
- [2026-08-01] 슬러그·ID 를 예측해서 참조를 미리 만들지 않는다 — 생성 → 실제 이름 확인 → 참조 연결 순서로 간다. 도구마다 슬러그 규칙이 다르고 비-ASCII 처리는 특히 갈린다. (근거: omc-wiki-page-authoring.md)
- [2026-08-01] 셸 변수에 담은 파일 목록을 `cmd -- $files` 로 넘기지 않는다 — zsh 는 따옴표 없는 확장에도 단어 분할을 하지 않아 여러 줄이 인자 하나로 뭉치고, 매칭 0건이 조용히 "차이 없음"으로 읽힌다. `"${(f)files}"` 를 쓰거나 pathspec 없이 `--name-status` 로 판정한다. (근거: verification-trigger-coverage.md)
- [2026-08-02] 스킬이 특정 경로·도구를 쓰라고 할 때, 그 경로에 대해 레포가 이미 내린 결정(ADR)이 있는지 먼저 본다 — 스킬의 기본 동작은 레포 사정을 모르고, 기각된 안을 되살릴 수 있다. (근거: omc-wiki-page-authoring.md)
- [2026-08-02] ref 를 비교하는 식은 양변이 같은 네임스페이스(원격/로컬)인지 확인한다 — `origin/X...Y` 처럼 한쪽만 원격이면 "원격에 있는가"를 보증하지 않고 조용히 약한 질문이 된다. (근거: gate-ref-symmetry.md)
- [2026-08-02] 안전장치가 통과했을 때 막아 준 근거가 설계인지 우연인지 구분한다 — "사고가 안 났다"는 게이트가 작동했다는 증거가 아니다. 게이트를 "무엇을 봤는가"가 아니라 "이 통과가 무엇을 보증하는가"로 옮겨 적어 본다. (근거: gate-ref-symmetry.md)
- [2026-08-02] squash 머지를 쓰는 레포에서 도달 가능성(`branch -d`·`git log A..B`·`git cherry`)으로 "머지됐나"를 판정하지 않는다 — 전부 "미머지"라고 답한다. (근거: gate-ref-symmetry.md)
- [2026-08-02] 로컬 도구가 답 못 하는 질문은 그 정보를 실제로 가진 상위 시스템(PR·CI·레지스트리)에 물을 수 있는지 먼저 본다 — 로컬 휴리스틱을 정교하게 깎는 것보다 물을 상대를 바꾸는 게 정확하다. 대신 그 시스템에 못 닿을 때의 폴백을 설계에 포함한다. (근거: gate-ref-symmetry.md)
- [2026-08-02] CLI 를 프로그램에서 부를 때 `--json` 필드도 플래그와 똑같이 설치된 버전에 있는지 확인한다 — `gh` 2.7.0 에는 `headRefOid` 가 없어 `commits[].oid` 로 우회했다. (근거: gate-ref-symmetry.md)
- [2026-08-02] 판정할 수 없는 것을 게이트로 만들려 하지 말고, 판정할 수 없다는 사실을 정확히 출력한다 — `✓` 는 보증이고, 보증 못 할 때 안 찍는 것이 오탐 비용 0으로 더 넓게 막는다. (근거: gate-ref-symmetry.md)
- [2026-08-02] 순수 함수 추출은 로직이 있는 곳에서만 한다 — 분기만 뽑으면 커버리지는 오르고 보증은 그대로다. "이 함수에서 틀릴 수 있는 게 무엇인가"에 답이 없으면 인라인이 맞고, 새 함수보다 기존 함수의 반환 타입을 넓히는 쪽이 먼저다. (근거: gate-ref-symmetry.md)
- [2026-08-02] 임시 레포 probe 는 결과만 보지 말고 "만들려던 상태가 만들어졌는지"를 함께 출력한다 — `git commit -am` 은 untracked 를 안 담고(`git add -A` 를 쓴다), `set -e` 는 `&&` 체인 끝의 실패를 항상 잡지 않아 fixture 가 조용히 어긋난 채 그럴싸한 출력이 나온다. (근거: gate-ref-symmetry.md)
