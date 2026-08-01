# Architecture Decision Records

## 철학
<이 프로젝트의 의사결정 원칙 한 단락>

---

### ADR-001: 파이프라인 phase 규칙 — 브랜치 이름과 compound 분리
**결정**: `/pipeline` 파이프라인에서 phase 브랜치는 입력한 이름(slug)을 대문자로 한 `<SLUG>`(예: `SHARE-FORTUNE`, `feat-` 접두어 없음)로 만든다. compound(교훈 기록, CLAUDE.md 5장)는 파이프라인 stage 에서 빼고 `/ce-compound` 로 수동 실행한다.
**이유**: 브랜치는 phase 이름과 1:1로 눈에 띄게 대응시키는 편이 추적이 쉽다. compound 는 사람이 회고를 판단해야 하는 단계라 자동화 stage 로 묶으면 형식적 기록만 남는다.
**트레이드오프**: compound 를 파이프라인 밖에 두면 빼먹을 수 있다 → make-pr 종료 시 `/ce-compound` 안내로 완화. 대문자 브랜치는 대소문자 구분 없는 파일시스템/툴에서 충돌 여지가 있으나 현재 워크플로우에선 문제 없음.

---

### ADR-002: 레포 자체를 Claude Code plugin(`harness`)으로 패키징
**결정**: 이 레포 루트에 `.claude-plugin/{plugin.json, marketplace.json}` 을 두어 레포 = plugin = marketplace 로 만든다. 스킬(pipeline·make-pr·make-issue)은 `skills/` 로 이동하고 `pipeline.py` 는 `skills/pipeline/scripts/` 에 번들한다. install-time 스크립팅이 없으므로 프로젝트 초기화는 `/harness:setup` 스킬이 담당한다: scope(글로벌=번들 스크립트+phases 만 / 프로젝트=pipeline.py·docs·CLAUDE.md 전부 복사)와 docs 경로를 물어 `.claude/harness.json` 에 저장하고, CLAUDE.md 는 마커(`<!-- harness:start/end -->`) append 만 한다. `plugin.json` 의 `version` 은 생략해 커밋 SHA 가 버전이 되게 한다. gstack 벤더 스킬(plan-ceo-review/plan-eng-review)은 plugin 에서 제외하고 `.claude/skills/` 에 남긴다.
**이유**: 레포 하나로 개발·배포·업데이트(`/plugin marketplace update`)가 끝난다. version 생략은 push=업데이트라 "쉬운 업데이트" 요구에 부합. CLAUDE.md append-only 는 사내 프로젝트의 기존 지침 보호. `pipeline.py` 의 ROOT 를 스크립트 위치 → cwd 기준 git root 로 바꿔 글로벌 캐시에서 실행해도 대상 레포에 phase 가 생기고 worktree 동작이 유지된다.
**트레이드오프**: 프로젝트 scope 로 복사된 `pipeline.py` 는 plugin 업데이트를 자동으로 받지 못한다 → setup 재실행으로 갱신 안내. plugin 활성화는 보안상 커밋 설정으로 공유 불가 → README 의 settings.local.json 안내로 완화(claude-plugin-config-scope.md 학습).

---

### ADR-003: harness 설정 저장소를 `.claude/harness.json` → `.claude/settings.local.json` 의 `env.HARNESS_*` 로 이전
**결정**: harness 설정(`scope`, `docsPath`)을 별도 파일 `.claude/harness.json` 대신 `.claude/settings.local.json` 의 `env` 키에 `HARNESS_SCOPE`/`HARNESS_DOCS_PATH` 환경변수로 저장한다. 스킬은 환경변수를 먼저 읽고, 없으면 파일의 `env` 객체를 직접 읽는다(setup 직후 세션 재시작 전에는 env 주입이 안 되므로). setup 은 이 파일을 merge 만 하고(기존 `enabledPlugins`·다른 env 변수 보존) 덮어쓰지 않는다.
**이유**: 설정 파일을 하나로 통합(plugin 활성화와 harness 설정이 같은 파일). `env` 는 settings 스키마가 지원하는 키라 unknown-key 경고가 없고, Claude Code 가 세션 환경변수로 주입해 스킬·스크립트가 JSON 파싱 없이 읽을 수 있다.
**트레이드오프**: settings.local.json 은 gitignore 대상이라 설정이 커밋/공유되지 않는다(기존 harness.json 은 커밋 대상이었음) → 팀원 각자 `/harness:setup` 을 한 번 실행해야 한다. 일부 도구/샌드박스 환경은 이 파일 쓰기를 제한한다 → setup 실행 시 권한 프롬프트가 뜰 수 있다.

---

### ADR-004: pipeline stage 재구성 — TDD splice·human gate·resume 전용 run (issue #7)
**결정**: pipeline stage 를 `discuss → plan → [ceo] → [eng] → approve → implement-red/green(TDD, 기본; --no-tdd 시 implement 단일) → verify → commit-push → make-pr` 로 재구성한다. red/green 은 `STAGES` 상수가 아니라 doc-build(`new_phase_doc`) 시 `implement` 자리에 splice 한다. discuss/approve 는 opt-out 없는 필수 human gate 다(계획 승인이 파이프라인의 목적이라 생략 대상이 아니다). headless `run` 은 resume 전용 헬퍼로 격하한다(discuss·approve·implement-red 직후 멈춘다). `verify` 는 `/verify` — `implement` 와 함께 oh-my-claudecode(OMC) 하드 의존이다. plan 산출물은 `phases/<slug>/plan.md` 로 커밋 대상화한다(`.gitignore` 를 `phases/*/*` + `!phases/*/plan.md` 로 재구성).
**이유**: 계획 승인 게이트·TDD·증거 기반 검증 단계 부재를 해소하면서 브랜치/worktree 병렬성을 유지한다.
**트레이드오프**: 모든 phase 에 human stop 2개(discuss/approve)가 추가된다 → 의도된 설계. `run` 자동화 범위가 축소된다 → resume 전용으로 문서화. OMC 의존을 명시화한다. CLAUDE.md §5 hook 승격 지침은 issue #7 과 무관한 사용자 요청 rider 로 별도 커밋한다.
**후속**: "plan 산출물을 `phases/<slug>/plan.md` 로 커밋 대상화한다(`.gitignore` 를 `phases/*/*` + `!phases/*/plan.md` 로 재구성)" 조항은 ADR-005 로 뒤집혔다.

---

### ADR-005: `phases/` 를 커밋 대상에서 제외하고 gitignore 규칙도 두지 않는다 (issue #11)
**결정**: `phases/<slug>/` 하위 전체(`plan.md` 포함)를 커밋하지 않는다. 동시에 `.gitignore` 에서 phases 관련 규칙(`phases/*/*` + `!phases/*/plan.md`)을 **제거**하고, `/harness:setup` 도 대상 레포에 `phases/` 를 뿌리지 않는다(gitignore 블록은 `.claude/worktrees/` + `.claude/settings.local.json` 두 줄). 방침은 도구가 아니라 CLAUDE.md §6 규범으로 강제한다. ADR-004 의 plan.md 커밋 대상화 조항을 대체한다.
**이유**: issue #11 은 setup 이 뿌린 `phases/` 가 plan.md 추적을 막는 문제였다. git 은 디렉토리가 제외되면 하위를 `!` 로 되살릴 수 없어 두 줄 + 재포함 트릭이 필요했고, 그 규칙을 대상 레포마다 정확히 전파하는 비용이 얻는 것보다 컸다. plan.md 를 커밋 대상에서 빼면 규칙 자체가 불필요해져 문제가 증상이 아니라 원인에서 사라진다.
**트레이드오프**: `phases/` 가 `git status` 에 항상 untracked 로 뜬다 → 의도된 상태로 CLAUDE.md §6 에 명시하고, `git add .` 금지·commit-push stage 의 범위 확인 절차로 오커밋을 막는다. plan.md 가 PR diff 에 안 보여 리뷰어가 계획 문서를 볼 수 없다 → PR 본문에 계획 요약을 넣는 것으로 대체. 검토했으나 버린 안: lefthook pre-commit 차단(대상 레포에 런타임 의존 강요, 설치 보장 불가), 상태 파일을 `.git/harness/<slug>/` 로 이동(`pipeline.py` 변경이 따라와 범위 초과 — 재검토 여지 있음).

---

### ADR-006: make-pr·make-issue 는 레포 템플릿을 읽고, 없을 때만 스킬 내장 형식으로 fallback (issue #12)
**결정**: 두 스킬이 본문을 만들기 전에 레포 템플릿을 탐색한다. PR 은 단일 파일(`.github`/`docs`/루트의 `pull_request_template.md`)과 다중 디렉토리(`.github/PULL_REQUEST_TEMPLATE/*.md`)를 모두 훑고, 이슈는 `.github/ISSUE_TEMPLATE/*.md` 와 레거시 단일 파일을 훑는다. 찾으면 헤딩 구조를 그대로 두고 내용만 채우고, 못 찾을 때만 스킬에 명시된 기본 형식을 쓴다. 이슈 템플릿은 `.md` 만 지원하고 `.yml`(Issue Forms)은 fallback 으로 보낸다. 라벨은 `gh label list` 로 존재를 확인해 있는 것만 붙이고, 없으면 조용히 생략한다(자동 생성하지 않는다). 탐색 명령은 `ls`+glob 이 아니라 `find` 로 통일한다.
**이유**: 스킬 서술("레포 템플릿 형식에 맞춰")과 실제 동작(하드코딩 본문)이 어긋나 있었다. harness 는 다른 레포에 설치되는 plugin 이라, 템플릿 구조가 다른 레포에서 조용히 틀린 본문을 만들어낸다. `gh pr create --template` 위임은 설치된 gh 2.7.0 에 없고 대화형 에디터 prefill 전용이라 비대화형 `--body` 흐름과 충돌해 탈락했다. 탐색 로직을 공유 문서로 DRY 화하는 안도 호출 지점이 2곳뿐이고 plugin 스킬이 각자 로드되어 상대 참조가 보장되지 않아 탈락했다. `find` 통일은 zsh 에서 glob 매칭 실패가 `2>/dev/null` 을 뚫고 에러를 내기 때문이다.
**트레이드오프**: `.yml` Issue Forms 를 쓰는 레포는 여전히 fallback 본문을 받는다 → 폼 파싱은 구조 변환이 필요해 범위에서 제외. 라벨을 조용히 생략하므로 의도한 라벨이 안 붙어도 사용자가 모를 수 있다 → 생성 전 최종 확인 단계에서 라벨을 함께 보여주는 것으로 완화. `gh label list --limit 100` 이라 라벨이 100개를 넘는 레포는 뒤쪽이 누락될 수 있다.
---

### ADR-007: 하드 의존 스킬 점검은 코드가 아니라 스킬 지침으로, init 이전에 한다 (issue #13)
**결정**: 파이프라인의 하드 의존 스킬(OMC `/plan`·`/ultrawork`·`/verify`, gstack plan review) 가용성 점검을 `pipeline.py` 코드가 아니라 `skills/pipeline/SKILL.md` §0-1 지침으로 둔다. 판정 근거는 에이전트 컨텍스트에 이미 주어지는 "사용 가능한 스킬 목록"이며, 표에는 목록에 뜨는 식별자(OMC 는 `oh-my-claudecode:` 접두어, gstack 은 무접두어)를 그대로 적는다. 위치는 `init` **이전** — worktree·브랜치 생성 전이라야 손해가 0이다. gstack 누락 시 plan review 를 "권유"가 아니라 **질문 자체에서 제거**하고 `--no-review` 로 고정한다. `STAGES` 주석에 §0-1 동시 갱신 cross-ref 를 둔다(`TDD_PAIR` 주석 선례).
**이유**: `~/.claude/plugins/cache/**` 등을 glob 하는 코드 점검은 plugin 캐시 경로 규칙·marketplace 이름·플러그인 활성화 여부에 종속돼 오탐과 누락이 모두 난다. 에이전트는 이미 정확한 목록을 갖고 있으므로 코드 0줄이 더 정확하다. 규범을 도구 대신 문서로 강제하는 것은 ADR-005 가 세운 이 레포의 선례다. 미설치는 선호가 아니라 제약이므로 고를 수 없는 선택지를 남기지 않는다(GUARDRAILS 2026-08-01).
**트레이드오프**: 지침 준수 여부를 기계적으로 검증할 수 없다 → 인정된 비용. 표가 `STAGES` 와 갈라질 수 있다 → 주석 cross-ref 로 완화. `make-pr`(harness 자기 자신)·`compound`(파이프라인이 항상 `--no-compound`)는 표에서 의도적으로 제외했다.
