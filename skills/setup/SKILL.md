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
유일한 예외는 프로젝트 scope 의 `scripts/pipeline.py` 예요 — 이건 plugin 번들의 복사본이라 갱신 대상이고,
확인을 받은 뒤에만 덮어써요 (§4 참고).

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

## 2. 사전 스캔 (쓰기 전 필수)

§1 의 답변이 나오면, **파일을 하나도 건드리기 전에** 대상 전체를 훑어 상태를 보여줘요.
재실행(플러그인 업데이트 후)에서 무엇이 그대로 남고 무엇이 바뀌는지 미리 알 수 있어야 해요.

> **이 표를 고치면 §3·§4·§5 의 해당 절차도 함께 갱신해요** — 판정 근거는 이 표에만 있어요.

scope 에 해당하는 행만 보여줘요.

| 대상 | scope | 판정 방법 | 상태 |
| --- | --- | --- | --- |
| `.claude/settings.local.json` 의 `env.HARNESS_*` | 공통 | 파일의 `env` 값 vs 이번 답변 | 없음/동일/다름 |
| `.gitignore` 의 `.claude/worktrees/` | 공통 | `grep -qxF` (줄 단위) | 없음/동일 |
| `.gitignore` 의 `.claude/settings.local.json` | 공통 | `grep -qxF` (줄 단위) | 없음/동일 |
| `.gitignore` 의 `phases/` 잔재 | 공통 | `grep -qxF 'phases/'` | 없음/다름 |
| `scripts/pipeline.py` | 프로젝트 | 헤더 SHA vs 번들 SHA (§4-1) | 없음/동일/다름/판정불가 |
| `<docs>/` 템플릿 5종 | 프로젝트 (글로벌은 원할 때만) | 파일 존재 여부만 | 없음/있음 |
| `CLAUDE.md` 마커 블록 | §1 에서 추가하기로 했을 때 | `<!-- harness:start -->` 존재 여부 | 없음/다름 |

`.gitignore` 두 줄은 **블록이 아니라 줄마다 따로** 봐요. 한 줄만 있는 레포가 실제로 있어서, 블록으로 보면
`없음`(둘 다 추가 → 중복)이나 `동일`(누락 방치) 어느 쪽으로도 틀려요.

### 상태

| 상태 | 뜻 | 처리 |
| --- | --- | --- |
| `없음` | 대상이 아직 없어요 | 묻지 않고 만들어요 |
| `동일` | 이미 최신이에요 | **묻지 않고** 건너뛰어요 |
| `다름` | 갱신 후보예요 | 아래 확인 프롬프트로 |
| `판정불가` | 비교할 근거가 없어요 | 갱신 후보에서 빼고 사유를 적어요 |

`판정불가` 는 지금 `scripts/pipeline.py` 한 행에만 생겨요 — 번들 SHA 를 읽을 자리가 12자리 hex 가 아니면
(= plugin 으로 설치한 게 아니면) 복사본이 낡았는지 **알 수 없어요.** 이때 `동일` 로 찍는 건 출처를 지어내는
것과 같으니, `판정불가 (plugin 설치 아님 — 출처 확인 불가)` 로 적고 그대로 둬요.

**`CLAUDE.md` 마커 행은 한 번 setup 을 돌린 레포에서 늘 `다름` 이에요.** 마커 존재 여부로만 판정하고
블록 내용을 템플릿과 비교하지 않기 때문이에요(그렇게 정한 이유는 §5 에 있어요). 그래서 이 행은
**§6 의 "모두 최신" 판정에서 제외해요** — 안 그러면 다른 게 전부 그대로여도 "모두 최신"이 영영 안 나와요.
확인 프롬프트에는 그대로 올라오니, 재실행마다 이 한 건을 확인하게 되는 건 의도된 비용이에요.

### 확인은 한 번만

**`다름` 이 1개 이상일 때만** AskUserQuestion 을 **한 번** 띄워요:

- `전부 갱신` / `골라서 갱신` / `전부 유지`
- `scripts/pipeline.py` 가 `다름` 이면서 그 파일에 **uncommitted 수정이 있으면**, 프롬프트에
  "로컬 수정이 있습니다 — 덮어쓰면 사라집니다"를 함께 띄워요.
- `.gitignore` 의 `phases/` 잔재는 "ADR-005 이후 불필요한 줄이에요" 근거를 함께 보여주고 **기본값은 `유지`** 예요.

`다름` 이 0개면 확인 프롬프트를 **띄우지 않아요.**

**이 스캔이 유일한 결정 지점이에요.** §3·§4·§5 는 각자 다시 묻지 않고 여기서 받은 결정을 적용만 해요.
결정 지점이 둘이면 같은 걸 두 번 묻게 되고, 두 서술이 조용히 갈라져요.

### 판정 명령

결과가 없을 때도 조용해야 해요. `ls` + glob 은 zsh 에서 매칭 0건이 `2>/dev/null` 을 뚫고 에러를 내니 쓰지 않아요.
`.gitignore`·`CLAUDE.md` 가 아예 없을 수 있으니 `test -f` 를 먼저 봐요.

```bash
test -f .gitignore && grep -qxF '.claude/worktrees/' .gitignore && echo 동일 || echo 없음
test -f .gitignore && grep -qxF 'phases/' .gitignore && echo 다름 || echo 없음
test -f <docs>/PRD.md && echo 있음 || echo 없음
test -f CLAUDE.md && grep -qF '<!-- harness:start -->' CLAUDE.md && echo 다름 || echo 없음
```

## 3. 설정 기록 (공통)

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

§2 가 이 행을 `다름` 으로 잡았고 사용자가 갱신을 골랐으면 갱신하고, `동일` 이면 건너뛰어요.
**여기서 따로 묻지 않아요** — 확인은 §2 에서 이미 받았어요.
(env 는 세션 시작 시 환경변수로 주입되므로, setup 직후 현재 세션에서는 스킬들이 파일을 직접 읽어 fallback 해요.)

`.gitignore` 에는 아래 두 줄 중 **§2 가 `없음` 으로 잡은 줄만** 추가해요 (있는 줄은 그대로 둬요):

```
.claude/worktrees/
.claude/settings.local.json
```

`phases/` 는 넣지 않아요. phase 산출물은 커밋 대상이 아니지만 무시 규칙도 두지 않고 규범으로 다뤄요
(CLAUDE.md 참고). **구본 setup 이 넣은 `phases/` 줄이 있으면** §2 가 `다름` 으로 잡아요 — 갱신을 고른
경우에만 그 줄을 지우고, 기본값인 `유지` 면 그대로 둬요.

## 4. scope 별 scaffold

templates 원본은 이 스킬 폴더의 `templates/` 에 있어요.
**복사할 때 파일 안의 `{{DOCS_PATH}}` 를 답변한 docs 경로로 치환해요** (`GUARDRAILS.md`·`solutions-README.md`·
`CLAUDE-section.md` 에 들어 있어요). 치환을 빠뜨리면 scaffold 가 없는 경로를 가리켜요.

**프로젝트 scope:**

1. 이 스킬 폴더 기준 `../pipeline/scripts/pipeline.py` 를 `<프로젝트>/scripts/pipeline.py` 로 복사하되,
   **출처 헤더 2줄을 넣어요**. 복사본은 plugin 업데이트를 자동으로 못 받으니, 파일 자신이 출처를 들고 있어야
   얼마나 낡았는지 알 수 있어요.

   **a. plugin SHA 확인.** 이 스킬의 base directory 는 `~/.claude/plugins/cache/harness/harness/<sha>/skills/setup`
   형태예요. `harness/harness/` 바로 다음 디렉토리명이 커밋 SHA(12자리 hex)예요. 캐시는 git 레포가 아니라
   `git rev-parse` 는 못 써요.
   **그 자리가 12자리 hex 가 아니면(= plugin 으로 설치된 게 아니면) 복사하지 말고 멈춰요.** 이렇게 안내해요:
   > pipeline.py 의 출처(plugin SHA)를 확인할 수 없어 프로젝트 scope 복사를 건너뜁니다.
   > 추적 불가능한 복사본은 만들지 않아요. plugin 으로 설치한 뒤 다시 실행하거나, 글로벌 scope 를 쓰세요.

   이 경우 §2 스캔에서도 이 행은 `판정불가` 예요. docs 템플릿(2번)은 그대로 진행해도 돼요.

   **b. 헤더 삽입.** shebang(`#!/usr/bin/env python3`) 바로 아래에 이 2줄을 넣어요. 날짜는 복사하는 날(`YYYY-MM-DD`):

   ```python
   # harness plugin <sha> 에서 복사 (<YYYY-MM-DD>) — 갱신: /harness:setup 재실행
   # 직접 수정하지 마세요 — 재실행 시 덮어쓰입니다.
   ```

   **이 2줄 외에는 원본을 한 글자도 바꾸지 않아요.** (주석이라 실행에 영향 없고, docstring 도 그대로 유지돼요.)

   **c. 이미 `scripts/pipeline.py` 가 있으면** §2 의 판정을 그대로 따라요. 판정은 헤더의 SHA 와 지금 번들
   SHA 를 비교하는 거예요(헤더가 없는 구본은 `다름`):
   - `동일` → 최신이니 건너뛰고 그렇다고 알려줘요.
   - `다름` → §2 에서 갱신을 골랐으면 덮어쓰고, 유지를 골랐으면 그대로 둬요. **여기서 다시 묻지 않아요.**
     (덮어쓰기 전 로컬 수정 경고는 §2 의 확인 프롬프트가 이미 띄웠어요.)
   - `판정불가` → 번들 SHA 를 못 구한 경우예요. 그대로 두고 사유만 알려줘요.

2. `<docsPath>/` 에 `templates/PRD.md`·`ADR.md`·`ARCHITECTURE.md` 복사, `<docsPath>/solutions/` 에 `templates/solutions-README.md`(→ `README.md`)·`templates/GUARDRAILS.md`(→ `GUARDRAILS.md`) 복사. **이미 있는 파일은 건너뛰고 뭘 건너뛰었는지 알려줘요. 내용은 비교하지 않아요** — 사용자가 채우는 문서라 재실행 시 항상 템플릿과 다르고, diff 는 노이즈일 뿐이에요.

**글로벌 scope:** 복사·scaffold 없음. docs 템플릿이 필요하면 원하는지 한 번 물어보고, 원할 때만 위 2번을 수행해요.

## 5. CLAUDE.md append (덮어쓰기 금지)

`templates/CLAUDE-section.md` 의 `{{DOCS_PATH}}` 를 답변한 docs 경로로 치환한 뒤, 마커로 감싸 **파일 끝에 append** 해요:

```markdown
<!-- harness:start -->
…치환된 템플릿 내용…
<!-- harness:end -->
```

- 대상 파일이 없으면 새로 만들어요. 있으면 **기존 내용은 그대로 두고 뒤에 추가**해요.
- append 전에 추가될 내용을 사용자에게 보여주고 확인받아요. (이건 §2 의 `없음` — 신규 생성 경로라 스캔의 갱신 대상이 아니에요.)
- 이미 `<!-- harness:start -->` 마커가 있으면 §2 가 `다름` 으로 잡아요. append 하지 않고, §2 에서 갱신을
  골랐으면 마커 사이 내용을 갱신하고 유지를 골랐으면 그대로 둬요. **여기서 다시 묻지 않아요.**
  (판정은 마커 존재 여부로만 해요 — 블록 내용을 템플릿과 비교하지는 않아요.)
- **글로벌 `~/.claude/CLAUDE.md` 에 append 하는 경우 `## Project Docs` @import 블록은 제외**해요 (프로젝트 상대 경로라 글로벌에선 깨져요).

## 6. 종료 안내 (반드시 출력)

### 이번 실행 결과 (파일 단위)

무엇을 했는지만큼 **무엇을 안 했고 왜인지**가 중요해요. 파일마다 한 줄씩 적어요:

```
생성  <docs>/solutions/GUARDRAILS.md
갱신  scripts/pipeline.py        (a1b2c3d4e5f6 → 2f4cb5449686)
스킵  CLAUDE.md                  (마커 있음 — 사용자가 유지 선택)
스킵  .gitignore                 (두 줄 모두 이미 있음)
스킵  <docs>/PRD.md              (이미 존재 — 사용자 문서, 내용 비교 안 함)
보류  scripts/pipeline.py        (판정불가 — plugin 설치 아님)
```

- `갱신` 은 무엇 → 무엇인지(SHA 등)를 적어요.
- `스킵` 은 **사유**를 적어요.
- **바뀐 게 하나도 없어도 이 블록을 출력하고 "모두 최신이에요" 라고 명시해요.** 아무 말도 안 하는 건
  "안 돌았음"과 구분이 안 돼요.
- **"모두 최신" 판정에서는 `CLAUDE.md` 마커 행을 빼고 봐요.** 그 행은 내용을 비교하지 않아 setup 을 한 번
  돌린 레포에서 늘 `다름` 이라(§2), 포함시키면 이 문구가 영영 못 나와요. 대신 아래처럼 한 줄로 따로 적어요:

```
나머지 모두 최신이에요 — 생성 0건 / 갱신 0건
스킵  .claude/settings.local.json  (HARNESS_* 값 동일)
스킵  .gitignore                   (두 줄 모두 이미 있음)
스킵  scripts/pipeline.py          (헤더 SHA = 번들 SHA)
스킵  <docs>/PRD.md 외 4건         (이미 존재 — 사용자 문서, 내용 비교 안 함)
확인  CLAUDE.md                    (마커 있음 — 내용을 비교하지 않아 매번 확인해요)
```

### 이어서 알아둘 것

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

- **의존 스킬**: `/harness:pipeline` 은 oh-my-claudecode(`/plan`·`/ultrawork`·`/verify`)와 gstack(plan review) 스킬을 써요. 없으면 해당 stage 가 막히는데, 파이프라인이 시작 전에 점검하고 안내해요.
- **업데이트**: `/plugin marketplace update` 만 하면 최신 커밋으로 갱신돼요. (프로젝트 scope 로 복사한 `scripts/pipeline.py` 는 자동 갱신되지 않아요. 파일 첫 줄들의 출처 헤더로 어느 SHA 에서 언제 복사했는지 확인할 수 있고, 갱신하려면 `/harness:setup` 을 다시 실행해요 — §2 스캔이 최신인지 판정해 줘요.)

## 주의

- 어떤 경우에도 기존 파일을 덮어쓰지 않아요. 충돌 시 항상 사용자에게 물어요 — 묻는 자리는 §2 한 곳이에요.
- `.claude/settings.json`(커밋 대상) 에는 plugin 활성화 키를 절대 넣지 않아요.
