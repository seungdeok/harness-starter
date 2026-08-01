---
name: make-issue
description: >
  GitHub 이슈를 생성해요. 다음 상황에서 활성화돼요:
  사용자가 "이슈 만들어줘", "이슈 등록해줘", "버그 등록", "버그 리포트",
  "기능 요청", "기능 제안", "make issue", "create issue", "파일 이슈"라고 말할 때.
  버그인지 기능인지 판단하고, 레포에 이슈 템플릿이 있으면 읽어서 그 구조로,
  없으면 기본 형식으로 `gh issue create`를 실행해요.
argument-hint: "<bug|feature> <제목> [설명]"
user-invocable: true
metadata:
  author: seungdeok
---

# make-issue

레포에 이슈 템플릿이 있으면 그 형식으로, 없으면 아래에 명시된 기본 형식으로 GitHub 이슈를 만들어요.

```
유형 판단(bug/feature) → 템플릿 탐색 → 본문 구성 → 라벨 확인 → 확인 → gh issue create
```

## 사전 조건

`gh`가 인증되어 있어야 해요. 실패하면 사용자에게 안내하세요:

```bash
gh auth status || echo "gh 인증이 필요해요: gh auth login -h github.com"
```

## 절차

### 1. 유형 판단 (bug vs feature)

- 인자 첫 값이 `bug`/`버그` → **버그**, `feature`/`기능` → **기능**.
- 명시가 없으면 사용자의 설명에서 판단해요. 애매하면 사용자에게 되물어요.
- 재현 절차·에러·"안 돼요" 류 → 버그. 새 화면·기능·"추가했으면" 류 → 기능.

### 2. 제목·본문 확보

- 제목이 없으면 사용자에게 요청해요.
- 설명이 부족하면 되물어 채워요. 절대 임의로 지어내지 마세요.

### 3. 템플릿 탐색

```bash
find .github/ISSUE_TEMPLATE -name '*.md' 2>/dev/null
find .github docs . -maxdepth 1 -iname 'ISSUE_TEMPLATE.md' 2>/dev/null
```

(`ls` + glob 은 zsh 에서 매칭이 없을 때 `2>/dev/null` 로도 안 막히는 에러를 내니 `find` 로 통일해요.)

- 후보가 **여러 개면** 1단계에서 판단한 유형(bug/feature)에 맞는 걸 골라요 — 파일명(`bug_report.md`·`feature_request.md` 등) 또는 frontmatter 의 `name`/`about` 으로 매칭해요. 애매하면 목록을 보여주고 사용자에게 물어요.
- `.yml`(Issue Forms)만 있으면 지원하지 않으니 아래 기본 형식으로 가요.

### 4. 본문 구성

**템플릿을 찾았으면** — 맨 위 `---` frontmatter 블록은 떼어내고, 남은 마크다운의 **헤딩 구조를 그대로 둔 채** 내용만 채워요.

- 헤딩을 추가·삭제·번역하지 않아요.
- HTML 주석(`<!-- ... -->`)은 작성 지침이니 따르되, 최종 본문에서는 지워요.
- frontmatter 의 `labels:` 가 있으면 그 값을 라벨 후보로 쓰고(유형 기본값보다 우선), `title:` 이 있으면 제목 접두어로 써요.

**못 찾았으면** — 아래 기본 형식을 써요.

**버그** — 라벨 후보 `bug`:

```markdown
## 버그 설명

<사용자가 설명한 버그 내용>

## 재현 절차
1. <1단계>
2. <2단계>
```

**기능** — 라벨 후보 `enhancement`:

```markdown
## 제안하는 기능

<사용자가 제안한 기능 내용>
```

### 5. 라벨 존재 확인

라벨 후보가 레포에 실제로 있는지 확인해요. 없는 라벨을 붙이면 `gh issue create` 가 실패해요:

```bash
gh label list --limit 100 | cut -f1
```

(`--json` 은 오래된 `gh` 에 없어서 실패해요. 위 형태는 버전 무관하게 라벨 이름만 뽑아요.)

- 존재하는 후보만 `--label` 로 붙여요.
- 하나도 없으면 **라벨을 만들지 말고** `--label` 옵션 자체를 빼고 실행해요.

### 6. 확인 후 생성

실행 전에 최종 **title / label / body**를 사용자에게 보여주고 확인받아요. 확인 후:

```bash
gh issue create --title "<제목>" --label "<존재하는 라벨>" --body "<본문>"
```

생성되면 반환된 이슈 URL을 사용자에게 알려줘요.

## 주의

- 라벨은 **레포에 존재하는 것만** 붙여요. 없으면 조용히 생략하고, 새로 만들지 않아요.
- 본문 구조는 **레포 템플릿이 우선**이에요. 템플릿이 없을 때만 위 기본 형식을 써요.
