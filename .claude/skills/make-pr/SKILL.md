---
name: make-pr
description: >
  현재 브랜치로 draft(초안) Pull Request를 레포 PR 템플릿 형식으로 생성해요.
  다음 상황에서 활성화돼요: 사용자가 "draft pr 만들어줘", "초안 PR", "PR 올려줘",
  "PR 만들어줘", "풀리퀘 열어줘", "make pr", "create draft pr", "open pr"라고 말할 때.
  `pull_request_template.md` 형식(개요·체크리스트)으로 `gh pr create --draft`를 실행해요.
argument-hint: "[제목]"
user-invocable: true
metadata:
  author: seungdeok
---

# make-pr

레포의 PR 템플릿(`.github/pull_request_template.md`) 형식에 맞춰 draft PR을 만들어요.

```
브랜치·변경 확인 → 문서 동기화 확인 → 개요 초안 → 확인 → gh pr create --draft
```

## 사전 조건

`gh`가 인증되어 있어야 해요. 실패하면 안내하세요:

```bash
gh auth status || echo "gh 인증이 필요해요: gh auth login -h github.com"
```

## 절차

### 1. 브랜치·변경 상태 확인

```bash
git branch --show-current
git status --porcelain
git log main..HEAD --oneline
```

- 현재 브랜치가 `main`이면 **중단**하고, 별도 브랜치가 필요하다고 안내해요.
- 커밋 안 된 변경이 있으면 사용자에게 커밋/스태시 여부를 물어요.
- 원격에 브랜치가 없으면 `gh pr create`가 자동 push하지만, 필요 시 `git push -u origin <branch>`를 안내해요.

### 2. 문서 동기화 확인 (PRD/ADR/ARCHITECTURE)

`src/`·설정·의존성이 바뀐 PR이면 `docs/PRD.md`·`docs/ADR.md`·`docs/ARCHITECTURE.md`가 최신인지 확인해요. **문서·주석만 바뀐 PR이면 이 단계는 건너뛰어요.**

```bash
git diff --name-only main..HEAD
```

무엇이 바뀌었는지에 따라 갱신 대상을 판단해요:

- **기능·사용자 흐름** 변경 → `docs/PRD.md`
- **기술 결정·의존성·트레이드오프** 변경 → `docs/ADR.md` (새 ADR 항목 추가/수정)
- **디렉토리·계층·데이터 흐름** 변경 → `docs/ARCHITECTURE.md`

해당하는 문서마다 사용자에게 **"갱신할까요?"**를 물어요. 갱신하기로 하면 그 문서를 수정하고 이번 브랜치에 커밋한 뒤 PR에 포함하고, "해당 없음"이면 그대로 진행해요.

### 3. 제목·개요 구성

- 제목이 인자로 없으면, `main..HEAD` 커밋 메시지에서 초안을 만들어 제안해요.
- 개요는 커밋 내역을 바탕으로 **무엇을·왜** 바꿨는지 요약해요.

### 4. 본문 구성 (템플릿 형식 준수)

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
gh pr create --draft --base main --title "<제목>" --body "<본문>"
```

생성되면 반환된 PR URL을 사용자에게 알려줘요.

## 주의

- 항상 `--draft`로 만들어요 (정식 전환은 사용자가 준비되면 `gh pr ready`).
- base는 `main`이에요.
- 본문은 반드시 `## 개요`·`## 체크리스트` 구조를 유지해요.
- 문서 동기화는 **코드/설정/의존성 변경이 있을 때만** 물어요 (문서·주석만 바뀐 PR은 스킵).
