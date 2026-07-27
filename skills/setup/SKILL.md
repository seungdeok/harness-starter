---
name: setup
description: >
  harness plugin 설치 마법사예요. plugin 설치 후 프로젝트에서 처음 한 번 실행해요.
  다음 상황에서 활성화돼요: 사용자가 "harness 설정", "harness 세팅", "하네스 설치",
  "harness setup", "파이프라인 세팅해줘"라고 말할 때, 또는 다른 harness 스킬이
  harness 설정(`.claude/settings.local.json` 의 `env.HARNESS_*`)이 없어서 안내했을 때.
  scope(프로젝트/글로벌)와 docs 경로를 묻고,
  CLAUDE.md는 절대 덮어쓰지 않고 append만 해요.
user-invocable: true
metadata:
  author: seungdeok
---

# setup — harness 설치 마법사

plugin 은 설치 시점에 스크립트를 못 돌리므로, 이 스킬이 프로젝트별 초기화를 대신해요.
결과물: `.claude/settings.local.json` 의 `env.HARNESS_*`(설정) + scope 에 따른 파일 scaffold.

**절대 규칙: 기존 파일을 덮어쓰지 않아요.** CLAUDE.md 는 append 만, scaffold 는 없는 파일만 생성.

## 1. 질문 (AskUserQuestion, 필수)

세 가지를 한 번에 물어요:

1. **scope** — 하네스 파일을 어디에 둘지
   - `글로벌` (기본): pipeline.py 는 plugin 번들(글로벌 캐시)을 그대로 사용. 프로젝트에는 phase 파일(`phases/`)만 생겨서 worktree 와 함께 움직여요. 프로젝트에 복사되는 코드 없음.
   - `프로젝트`: `pipeline.py`·docs 템플릿·CLAUDE.md 섹션을 모두 프로젝트 내부에 복사/생성. 사내 레포처럼 모든 것을 레포 안에 커밋해야 할 때.
2. **docs 경로** — PRD/ADR/ARCHITECTURE 와 solutions(교훈 노트)를 둘 경로. 기본 `docs`. 사용자가 자유 입력으로 바꿀 수 있어요 (예: `documents`, `docs/harness`).
3. **CLAUDE.md 처리** — 행동 가이드라인(1~5장) 섹션을 어디에 추가할지
   - `프로젝트 CLAUDE.md 에 append` (기본)
   - `글로벌 ~/.claude/CLAUDE.md 에 append`
   - `건너뛰기`

## 2. 설정 기록 (공통)

`.claude/settings.local.json` 의 `env` 에 harness 설정을 **merge** 해요 (gitignore 대상 — 개발자 로컬 전용,
팀원도 각자 setup 을 실행해야 해요). 파일이나 `env` 키가 이미 있으면 기존 키(예: `enabledPlugins`, 다른
env 변수)는 그대로 두고 `HARNESS_*` 만 추가/갱신해요. 덮어쓰기 금지:

```json
{
  "env": {
    "HARNESS_SCOPE": "global|project",
    "HARNESS_DOCS_PATH": "<답변한 경로>"
  }
}
```

이미 `HARNESS_*` 값이 있으면 현재 값을 보여주고 갱신 여부를 확인해요.
(env 는 세션 시작 시 환경변수로 주입되므로, setup 직후 현재 세션에서는 스킬들이 파일을 직접 읽어 fallback 해요.)

`.gitignore` 에 아래 세 줄이 없으면 추가해요 (있는 줄은 건너뜀):

```
phases/
.claude/worktrees/
.claude/settings.local.json
```

## 3. scope 별 scaffold

templates 원본은 이 스킬 폴더의 `templates/` 에 있어요.

**프로젝트 scope:**
1. 이 스킬 폴더 기준 `../pipeline/scripts/pipeline.py` 를 `<프로젝트>/scripts/pipeline.py` 로 복사.
2. `<docsPath>/` 에 `templates/PRD.md`·`ADR.md`·`ARCHITECTURE.md` 복사, `<docsPath>/solutions/` 에 `templates/solutions-README.md`(→ `README.md`)·`templates/GUARDRAILS.md`(→ `GUARDRAILS.md`) 복사. **이미 있는 파일은 건너뛰고 뭘 건너뛰었는지 알려줘요.**

**글로벌 scope:** 복사·scaffold 없음. docs 템플릿이 필요하면 원하는지 한 번 물어보고, 원할 때만 위 2번을 수행해요.

## 4. CLAUDE.md append (덮어쓰기 금지)

`templates/CLAUDE-section.md` 의 `{{DOCS_PATH}}` 를 답변한 docs 경로로 치환한 뒤, 마커로 감싸 **파일 끝에 append** 해요:

```markdown
<!-- harness:start -->
…치환된 템플릿 내용…
<!-- harness:end -->
```

- 대상 파일이 없으면 새로 만들어요. 있으면 **기존 내용은 그대로 두고 뒤에 추가**해요.
- append 전에 추가될 내용을 사용자에게 보여주고 확인받아요.
- 이미 `<!-- harness:start -->` 마커가 있으면 append 하지 않고, 마커 사이 내용을 갱신할지 물어봐요.
- **글로벌 `~/.claude/CLAUDE.md` 에 append 하는 경우 `## Project Docs` @import 블록은 제외**해요 (프로젝트 상대 경로라 글로벌에선 깨져요).

## 5. 종료 안내 (반드시 출력)

설정 완료 후 아래를 요약해서 알려줘요:

- **docs 경로 진행 방식**: 답변한 경로가 `.claude/settings.local.json` 의 `env.HARNESS_DOCS_PATH` 에 저장됐고, make-pr(문서 동기화)·compound(교훈 기록) 등 harness 스킬이 이 값을 읽어요. 바꾸려면 이 파일을 수정하거나 `/harness:setup` 을 다시 실행하면 돼요. 이 파일은 gitignore 대상이라 팀원도 각자 `/harness:setup` 을 한 번 실행해야 해요.
- **plugin 활성화 공유**: 팀원도 쓰려면 각자 `.claude/settings.local.json` 에 활성화 설정을 넣어야 해요 (커밋되는 `.claude/settings.json` 에 넣으면 보안상 무시돼요):

  ```json
  {
    "enabledPlugins": { "harness@harness": true },
    "extraKnownMarketplaces": {
      "harness": { "source": { "source": "github", "repo": "seungdeok/harness-starter" } }
    }
  }
  ```

- **업데이트**: `/plugin marketplace update` 만 하면 최신 커밋으로 갱신돼요. (프로젝트 scope 로 복사한 `scripts/pipeline.py` 는 자동 갱신되지 않으니, 갱신하려면 `/harness:setup` 을 다시 실행해요.)

## 주의

- 어떤 경우에도 기존 파일을 덮어쓰지 않아요. 충돌 시 항상 사용자에게 물어요.
- `.claude/settings.json`(커밋 대상) 에는 plugin 활성화 키를 절대 넣지 않아요.
