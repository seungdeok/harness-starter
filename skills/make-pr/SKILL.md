---
name: make-pr
description: >
  현재 브랜치로 draft(초안) Pull Request를 생성해요.
  다음 상황에서 활성화돼요: 사용자가 "draft pr 만들어줘", "초안 PR", "PR 올려줘",
  "PR 만들어줘", "풀리퀘 열어줘", "make pr", "create draft pr", "open pr"라고 말할 때.
  레포에 PR 템플릿이 있으면 읽어서 그 구조로, 없으면 기본 형식(개요·체크리스트)으로
  `gh pr create --draft`를 실행해요.
argument-hint: "[제목]"
user-invocable: true
metadata:
  author: seungdeok
---

# make-pr

레포에 PR 템플릿이 있으면 그 형식으로, 없으면 아래에 명시된 기본 형식으로 draft PR을 만들어요.

```
템플릿 탐색 → 브랜치·변경 확인 → stacked PR 여부(리뷰 단위 2+) → 문서 동기화 확인 → 본문 작성 → 확인 → gh pr create --draft
                                 └─ 예: gh-stack (gh stack init/submit)
```

## 사전 조건

`gh`가 인증되어 있어야 해요. 실패하면 안내하세요:

```bash
gh auth status || echo "gh 인증이 필요해요: gh auth login -h github.com"
```

## 절차

### 0. base 브랜치·docs 경로·PR 템플릿 결정

- **base 브랜치**: `gh repo view --json defaultBranchRef -q .defaultBranchRef.name` 으로 감지해요 (실패 시 `main`). 아래의 `<base>` 는 전부 이 값이에요.
- **docs 경로**: 환경변수 `HARNESS_DOCS_PATH` 를 읽고, 없으면 `.claude/settings.local.json` 의 `env.HARNESS_DOCS_PATH` 를 읽어요 (둘 다 없으면 `docs`). 아래의 `<docsPath>` 는 이 값이에요.
- **PR 템플릿**: GitHub 이 인식하는 위치를 훑어요 — 단일 파일과 다중 템플릿 디렉토리 둘 다예요:

  ```bash
  find .github docs . -maxdepth 1 -iname 'pull_request_template.md' 2>/dev/null
  find .github/PULL_REQUEST_TEMPLATE -name '*.md' 2>/dev/null
  ```

  (`ls` + glob 은 zsh 에서 매칭이 없을 때 `2>/dev/null` 로도 안 막히는 에러를 내니 `find` 로 통일해요.)

  - 후보가 **하나면** 그 파일을 읽어서 써요.
  - **여러 개면** 목록을 보여주고 어느 템플릿을 쓸지 사용자에게 물어요.
  - **없으면** 절차 4 의 기본 형식으로 가요.

### 1. 브랜치·변경 상태 확인

```bash
git branch --show-current
git status --porcelain
git log <base>..HEAD --oneline
```

- 현재 브랜치가 `<base>`면 **중단**하고, 별도 브랜치가 필요하다고 안내해요.
- 커밋 안 된 변경이 있으면 사용자에게 커밋/스태시 여부를 물어요.
- 원격에 브랜치가 없으면 `gh pr create`가 자동 push하지만, 필요 시 `git push -u origin <branch>`를 안내해요.

### 1.5 stacked PR 여부 (opt-in)

판단 기준은 커밋 개수가 아니라 **리뷰 단위(관심사)가 2개 이상으로 나뉘는지**예요. `git log <base>..HEAD --oneline` 과 변경 파일을 보고, 커밋들이 의존 순서가 있는 계층(예: 모델 → API → UI)으로 묶일 때만 AskUserQuestion 으로 "stacked PR로 나눌까요?"를 물어요. 커밋이 많아도 전부 한 관심사면 묻지 않고 단일 PR로 가요.

- **아니오 (기본)** → 아래 2~5 그대로 진행 (단일 draft PR).
- **예** → 절차 2(문서 동기화)까지는 그대로 수행하고, 절차 3~5 대신 아래 **gh-stack 흐름**으로 생성해요.

  주의: `gh stack` 명령은 인자 없이 실행하면 대화형 프롬프트에 걸려 멈춰요. 반드시 아래처럼 브랜치 이름·플래그를 붙여요.

  1. 확장 설치 확인 — 없으면 안내하고 설치받아요:

     ```bash
     gh extension list | grep -qi gh-stack || echo "설치 필요: gh extension install github/gh-stack"
     git config rerere.enabled true   # init 시 대화형 프롬프트 방지
     ```

  2. 커밋을 관심사(계층) 단위로 묶어 **어떤 커밋이 어느 계층인지 사용자에게 보여주고 확인**받아요. 하위 계층(기반 코드)이 아래, 의존하는 코드가 위예요.
  3. 계층 경계 커밋마다 브랜치를 만들어요 — 마지막 계층은 현재 브랜치를 그대로 써요:

     ```bash
     git branch <계층1-브랜치> <계층1 마지막 커밋 SHA>
     git branch <계층2-브랜치> <계층2 마지막 커밋 SHA>
     ```

  4. 아래→위 순서로 스택을 만들고 draft PR을 생성해요 (제목은 커밋 메시지에서 자동 생성):

     ```bash
     gh stack init <계층1-브랜치> <계층2-브랜치> <현재-브랜치>
     gh stack submit --auto
     ```

  5. `gh stack view --json` 으로 결과를 확인하고 PR URL들을 사용자에게 알려주고 종료해요. 제목·본문을 다듬으려면 `gh pr edit <번호>` 를 안내해요.
  6. `submit` 이 exit code 9 로 실패하면 레포에 stacked PR 기능이 꺼져 있는 거예요 — 사용자에게 알리고 단일 draft PR 흐름(3~5)으로 돌아가요.

### 2. 문서 동기화 확인 (PRD/ADR/ARCHITECTURE)

`src/`·설정·의존성이 바뀐 PR이면 `<docsPath>/PRD.md`·`<docsPath>/ADR.md`·`<docsPath>/ARCHITECTURE.md`가 최신인지 확인해요. **문서·주석만 바뀐 PR이거나, 해당 문서 파일이 프로젝트에 없으면 이 단계는 건너뛰어요.**

```bash
git diff --name-only <base>..HEAD
```

무엇이 바뀌었는지에 따라 갱신 대상을 판단해요:

- **기능·사용자 흐름** 변경 → `<docsPath>/PRD.md`
- **기술 결정·의존성·트레이드오프** 변경 → `<docsPath>/ADR.md` (새 ADR 항목 추가/수정)
- **디렉토리·계층·데이터 흐름** 변경 → `<docsPath>/ARCHITECTURE.md`

해당하는 문서마다 사용자에게 **"갱신할까요?"**를 물어요. 갱신하기로 하면 그 문서를 수정하고 이번 브랜치에 커밋한 뒤 PR에 포함하고, "해당 없음"이면 그대로 진행해요.

### 3. 제목·개요 구성

- 제목이 인자로 없으면, `<base>..HEAD` 커밋 메시지에서 초안을 만들어 제안해요.
- 개요는 커밋 내역을 바탕으로 **무엇을·왜** 바꿨는지 요약해요.

### 4. 본문 구성

**절차 0 에서 템플릿을 찾았으면** — 그 파일의 **섹션 헤딩과 체크리스트 항목을 그대로 둔 채** 내용만 채워요.

- 헤딩을 추가·삭제·번역·재배열하지 않아요. 레포의 구조가 정답이에요.
- HTML 주석(`<!-- ... -->`)은 작성 지침이니 따르되, 최종 본문에서는 지워요.
- 해당 없는 섹션은 헤딩을 지우지 말고 "해당 없음" 으로 채워요.

**못 찾았으면** — 아래 기본 형식을 써요:

```markdown
## 개요

<변경 내용 요약>

## 체크리스트
- [ ] 동작 확인 완료
- [ ] 문서(PRD/ADR/ARCHITECTURE) 영향 확인 — 갱신 또는 해당 없음
```

### 5. 확인 후 생성

실행 전에 최종 **title / body**를 사용자에게 보여주고 확인받아요. 확인 후:

```bash
gh pr create --draft --base <base> --title "<제목>" --body "<본문>"
```

생성되면 반환된 PR URL을 사용자에게 알려줘요.

## 주의

- 항상 `--draft`로 만들어요 (정식 전환은 사용자가 준비되면 `gh pr ready`).
- stacked PR은 **opt-in**이에요 — 리뷰 단위가 2개 이상으로 나뉠 때만 묻고, 기본은 항상 단일 draft PR이에요.
- base는 원격 기본 브랜치예요 (감지 실패 시 `main`).
- 본문 구조는 **레포 템플릿이 우선**이에요. 템플릿이 없을 때만 `## 개요`·`## 체크리스트` 기본 형식을 써요.
- 문서 동기화는 **코드/설정/의존성 변경이 있을 때만** 물어요 (문서·주석만 바뀐 PR은 스킵).
