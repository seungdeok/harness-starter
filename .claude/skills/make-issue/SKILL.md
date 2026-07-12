---
name: make-issue
description: >
  GitHub 이슈를 레포 템플릿 형식으로 생성해요. 다음 상황에서 활성화돼요:
  사용자가 "이슈 만들어줘", "이슈 등록해줘", "버그 등록", "버그 리포트",
  "기능 요청", "기능 제안", "make issue", "create issue", "파일 이슈"라고 말할 때.
  버그(bug_report)인지 기능(feature_request)인지 판단해 해당 템플릿 구조와
  라벨로 `gh issue create`를 실행해요.
argument-hint: "<bug|feature> <제목> [설명]"
user-invocable: true
metadata:
  author: seungdeok
---

# make-issue

레포의 이슈 템플릿(`.github/ISSUE_TEMPLATE/`) 형식에 맞춰 GitHub 이슈를 만들어요.

```
유형 판단(bug/feature) → 본문 구성 → 확인 → gh issue create
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

### 3. 본문 구성 (템플릿 형식 준수)

**버그** — 라벨 `bug`:

```markdown
## 버그 설명

<사용자가 설명한 버그 내용>

## 재현 절차
1. <1단계>
2. <2단계>
```

**기능** — 라벨 `enhancement`:

```markdown
## 제안하는 기능

<사용자가 제안한 기능 내용>
```

### 4. 확인 후 생성

실행 전에 최종 **title / label / body**를 사용자에게 보여주고 확인받아요. 확인 후:

```bash
gh issue create --title "<제목>" --label "<bug|enhancement>" --body "<본문>"
```

생성되면 반환된 이슈 URL을 사용자에게 알려줘요.

## 주의

- 라벨은 유형에 맞게만 붙여요 (`bug` 또는 `enhancement`).
- 본문은 반드시 위 템플릿 헤더 구조를 유지해요.
