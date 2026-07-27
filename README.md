# harness-starter

Compound Engineering **phase pipeline 하네스**. Claude Code **plugin(`harness`)** 으로 설치해
어느 레포에서든 `plan → plan-review → implement → commit → make-pr` 루프를 돌릴 수 있어요.

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
| 전자동(headless) | "이 phase **끝까지 자동으로 돌려**" |

자세한 내용은 `docs/solutions/pipeline.md`.

## 필요한 스킬 (optional)

각 stage는 스킬을 실행해요. plugin 에 없는 아래 두 개는 외부에서 켜야 해요 — 없으면 그 stage만 건너뛰면 돼요.

| stage | 스킬 | 출처 |
| --- | --- | --- |
| plan-review-ceo/eng | `/plan-ceo-review`·`/plan-eng-review` | **gstack** |
| compound | `/ce-compound` (+ `/ce-code-review`) | **compound-engineering@compound-engineering-plugin** |

## 이 레포에서 개발 (dogfooding)

plugin 스킬은 `skills/` 로 옮겨져 이 레포의 `.claude/skills/` 에는 없어요. 이 레포 안에서
직접 써보려면 로컬 로드로 실행해요:

```bash
claude --plugin-dir .
```

수정 후에는 `/reload-plugins`, 매니페스트 검증은 `claude plugin validate .`.
