# harness-starter

Compound Engineering **phase pipeline 하네스**. Claude Code **plugin(`harness`)** 으로 설치해
어느 레포에서든 `discuss → plan → plan-review → approve → implement(TDD) → verify → commit → make-pr`
루프를 돌릴 수 있어요.

## 무엇을 위한 것인가

**에이전트 한 명이 작업 하나(phase)를** 요구사항 정리부터 draft PR 까지 끝내게 하는 하네스예요.
여러 에이전트를 동시에 지휘하는 오케스트레이션 도구가 아니라, phase 하나 = 브랜치/worktree 하나 =
세션 하나가 기본 단위예요.

- 진행 상태는 `phases/<slug>/phase.json` 이 기억해요 → 세션이 끊겨도 `status` 로 이어서 진행.
- 사람이 반드시 개입하는 지점(`discuss`·`approve`·커밋 범위 확인)은 생략할 수 없어요 — 승인 게이트가 이 파이프라인의 목적이에요.
- phase 를 여러 개 병행하고 싶으면 각각 **전용 worktree** 로 따로 시작해요(기본값).
- `phases/` 아래 산출물은 **커밋하지 않아요**. `git status` 에 untracked 로 계속 뜨는 게 정상이고,
  그래서 커밋할 때 `git add .` / `-A` 대신 파일을 명시해요 (ADR-005).

## 설치 (Claude Code plugin)

```
/plugin marketplace add seungdeok/harness-starter
/plugin install harness@harness
```

설치 후 대상 프로젝트에서 **설치 마법사**를 한 번 실행해요:

```
/harness:setup
```

setup 이 아래 세 가지를 묻고 초기화해요:

| 질문 | 선택지 |
| --- | --- |
| **scope** | **글로벌**(기본): pipeline.py 는 plugin 번들 사용, 프로젝트엔 `phases/` 만 생김(worktree 호환) · **프로젝트**: pipeline.py·docs·CLAUDE.md 섹션 전부 프로젝트 내부에 복사(사내 레포용) |
| **docs 경로** | PRD/ADR/ARCHITECTURE·solutions 위치, 기본 `docs` (자유 입력) |
| **CLAUDE.md** | 프로젝트 CLAUDE.md 에 append / 글로벌 `~/.claude/CLAUDE.md` 에 append / 건너뛰기 — **덮어쓰기는 절대 안 해요** |

## 업데이트

`version` 필드를 생략해 **커밋 SHA 가 버전**이에요. 새 커밋이 push 되면:

```
/plugin marketplace update
```

만 실행하면 최신으로 갱신돼요. (프로젝트 scope 로 복사한 `scripts/pipeline.py` 는 `/harness:setup` 재실행으로 갱신)

무엇이 바뀌었는지는 [`CHANGELOG.md`](CHANGELOG.md) 에서 확인해요.

## docs 경로 가이드

- setup 에서 답한 경로가 `.claude/settings.local.json` 의 `env.HARNESS_DOCS_PATH` 에 저장돼요 (gitignore 대상 — 개발자 로컬 전용, 팀원도 각자 setup 실행).
- `make-pr`(문서 동기화 확인), compound(교훈 기록) 등 harness 스킬이 이 값을 읽어요 (환경변수 우선, 파일 fallback).
- 변경 방법: `.claude/settings.local.json` 을 직접 수정하거나 `/harness:setup` 재실행.

```json
{
  "env": { "HARNESS_SCOPE": "global", "HARNESS_DOCS_PATH": "docs" }
}
```

## 팀원과 공유

plugin 활성화 설정은 보안상 커밋되는 `.claude/settings.json` 에 넣을 수 없어요
(무시됨 — `docs/solutions/claude-plugin-config-scope.md` 참고). 팀원 각자
`.claude/settings.local.json`(gitignore 됨) 에 넣어요:

```json
{
  "enabledPlugins": { "harness@harness": true },
  "extraKnownMarketplaces": {
    "harness": { "source": { "source": "github", "repo": "seungdeok/harness-starter" } }
  }
}
```

## 들어있는 것

| 파일 | 역할 |
| ---- | ---- |
| `.claude-plugin/plugin.json`·`marketplace.json` | plugin/marketplace 매니페스트 (이 레포 자체가 plugin) |
| `skills/pipeline/` | phase 파이프라인 스킬 + `scripts/pipeline.py`(의존성 0 stage 체커, cwd 기준 git root 에 `phases/<slug>/phase.json` 생성) |
| `skills/make-pr/`·`skills/make-issue/` | draft PR / 이슈 생성 스킬 |
| `skills/setup/` | 설치 마법사 + scaffold 템플릿(PRD/ADR/ARCHITECTURE·solutions·CLAUDE 섹션) |
| `.claude/skills/` | gstack 벤더 스킬 `plan-ceo-review`·`plan-eng-review` (plugin 미포함, 이 레포 전용) |
| `.claude/settings.json` | 위험 명령 차단 훅 |
| `docs/`·`CLAUDE.md` | 이 레포 자체의 문서/가이드라인 (scaffold 원본은 `skills/setup/templates/`) |

## 퀵스타트

Claude에게 시키면 돼요:

> **"<기능명> phase 파이프라인으로 작업 시작해줘"**

| 하고 싶은 것 | 이렇게 말하면 |
| --- | --- |
| 시작 | "결제 연동 기능 **phase 파이프라인으로 시작**해줘" |
| plan-review 생략 | "댓글 기능 phase로 시작하되 **plan review는 빼줘**" |
| 다음 stage | "**다음 stage 진행해**" / "advance 해줘" |
| 현재 위치 | "**지금 어느 stage야?**" |
| TDD 생략 | "이 phase는 **TDD 빼고** 시작해줘" |
| 자동 이어가기(headless) | "approve 이후 구간 **run으로 이어서 돌려**" (`run`은 resume 전용 — discuss·approve·implement-red 직후·commit-push에서 멈춰요) |

자세한 내용은 `docs/solutions/pipeline.md`.

## 사전조건 (필요한 스킬)

각 stage는 스킬을 실행해요. plugin 에 없는 스킬은 외부에서 켜야 해요.
파이프라인은 **init(worktree·브랜치 생성) 전에** 이 목록을 점검하고, 없는 게 있으면 먼저 알려줘요 (ADR-007).

**필수 (required)** — plan·implement(-red/green)·verify stage 가 하드 의존해요. 대안이 없어요 (ADR-004):

| stage | 스킬 | 출처 |
| --- | --- | --- |
| plan·implement(-red/green)·verify | `/plan`·`/ultrawork`·`/verify` | **oh-my-claudecode (OMC)** |

**선택 (optional)** — 없어도 파이프라인은 돌아가요:

| stage | 스킬 | 출처 | 없으면 |
| --- | --- | --- | --- |
| plan-review-ceo/eng | `/plan-ceo-review`·`/plan-eng-review` | **gstack** | `--no-review` 로 고정 (묻지 않아요) |
| compound (파이프라인 밖) | `/ce-compound`·`/ce-code-review` | **compound-engineering@compound-engineering-plugin** | 교훈 기록을 손으로 `docs/solutions/` 에 씀 |
| `done` 의 머지 판정 | `gh` CLI | GitHub CLI | 노트 내용 비교로 자동 폴백 |

## 파이프라인 이후 — compound 와 정리

make-pr 로 파이프라인은 끝나지만 작업은 안 끝나요. **리뷰까지 마쳤으면** 이번에 배운 걸 남겨요
(CLAUDE.md §5): `/ce-compound` → `docs/solutions/<slug>.md`, 일반화되는 규칙이면 `GUARDRAILS.md` 한 줄.

전용 worktree 는 **PR 이 머지된 뒤** 정리해요:

```bash
cd <메인 레포 루트> && python3 <pipeline.py> done <slug>
```

`done` 은 지우기 전에 교훈이 `origin/<base>` 에 **도착**했는지 봐요 — 브랜치가 `docs/solutions/` 를
건드렸는지(귀속), 그리고 `gh` 로 PR 이 실제 머지됐고 그 뒤에 붙은 커밋이 없는지(도착). 하나라도
어긋나면 **아무것도 지우지 않고 거부**해요 (`--force` 로 우회). 교훈을 push·머지하지 않은 채
worktree 를 날리면 그 작업이 아무것도 남기지 못하니까요 (ADR-012).

`git branch -d` 는 squash 머지를 미머지로 보기 때문에 브랜치가 남는 건 흔한 정상 상황이에요.
그때는 `✓ 정리 완료` 대신 확인 명령을 안내하니, 확인 전에 `-D` 로 지우지 마세요.

## 이 레포에서 개발 (dogfooding)

plugin 스킬은 `skills/` 로 옮겨져 이 레포의 `.claude/skills/` 에는 없어요. 이 레포 안에서
직접 써보려면 로컬 로드로 실행해요:

```bash
claude --plugin-dir .
```

수정 후에는 `/reload-plugins`, 매니페스트 검증은 `claude plugin validate .`.
