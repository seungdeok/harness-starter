---
title: "shell and CLI environment traps — zsh glob · gh 버전 · Projects classic"
tags: ["zsh", "shell", "gh-cli", "skill", "verification"]
created: 2026-08-01T14:26:09.581Z
updated: 2026-08-01T14:26:09.581Z
sources: []
links: ["ci-coverage-facts-validate.md", "harness-plugin-scope-marketplace-sha.md"]
category: environment
confidence: medium
schemaVersion: 1
---

# shell and CLI environment traps — zsh glob · gh 버전 · Projects classic

스킬·문서에 셸 명령을 써 넣을 때 실제로 터진 것들. 근거: `docs/solutions/skill-prose-commands.md` (PR #20), `docs/solutions/ci-check-coverage.md` (PR #18)

## 전제 — 스킬 문서의 셸 명령은 검증되지 않은 코드다

스킬에는 테스트 스위트가 없고 CI(`claude plugin validate`)도 `SKILL.md` 본문을 쳐다보지 않는다. 산문 안에 있다는 이유로 아무도 실행해 보지 않으므로, 여기 적힌 명령은 **사실상 미검증 상태로 배포된다.**

게다가 plugin 은 **남의 레포·남의 환경에서 돈다.** "우리 레포에서 잘 된다"는 검증이 아니다.

## zsh 의 glob nomatch 는 `2>/dev/null` 을 뚫는다

```bash
ls .github/ISSUE_TEMPLATE/*.md 2>/dev/null
# zsh: (eval):4: no matches found: .github/ISSUE_TEMPLATE/*.md
```

에러를 내는 주체가 `ls` 가 아니라 **셸**이다. 리다이렉션은 `ls` 의 stderr 에만 걸리므로 셸의 nomatch 는 그대로 새어 나온다. bash 에서는 glob 이 그대로 넘어가 `ls` 가 조용히 실패하니 **zsh 에서만 터진다.**

**대응**: 매칭이 없을 수 있는 조회는 `find` 로 통일한다. `find` 는 셸 glob 을 쓰지 않으므로 문제 자체가 없다.

```bash
find .github docs . -maxdepth 1 -iname 'pull_request_template.md' 2>/dev/null
find .github/PULL_REQUEST_TEMPLATE -name '*.md' 2>/dev/null
```

## `gh` 플래그는 설치된 버전에 있는지 확인한다

`gh label list --json` 은 최신 문서에는 있지만 **설치된 2.7.0 에는 없다.**

```bash
gh label list --help   # FLAGS: -L/--limit, -w/--web  ← --json 없음
```

**대응**: 버전 무관한 형태로 쓴다.

```bash
gh label list --limit 100 | cut -f1
```

## `gh issue view` / `gh pr edit` 의 Projects classic 에러

```
GraphQL: Projects (classic) is being deprecated ... (repository.issue.projectCards)
```

서브커맨드가 응답에 `projectCards` 를 함께 요청해서 나는 에러라 **인자로는 못 피한다.** `gh api` 로 우회한다.

```bash
gh api repos/<owner>/<repo>/issues/15 --jq '{number,title,body}'
gh api repos/<owner>/<repo>/pulls/18 -X PATCH -F body=@body.md
```

`gh pr create` · `gh pr checks` · `gh api` 는 정상 동작한다.

## 검증 절차 — 두 상태로 실행한다

"찾으면 A, 없으면 B" 분기를 적었다면 **두 경로를 모두 밟는다.** 결함은 대부분 **없음** 쪽에 숨어 있고, 성공 경로만 확인하면 안 보인다.

| 상태 | 기대 | 수정 전 실제 |
| --- | --- | --- |
| 템플릿 없음 | 에러 없이 빈 결과 → fallback | nomatch 에러 |
| 템플릿 있음 (임시 scaffold) | 경로 4개 모두 검출 | ✅ |
| 라벨 조회 | 라벨 이름 목록 | unknown flag |

임시 scaffold 는 레포를 건드리지 않게 `$TMPDIR` 에 만들어 돌린다.

## 서술과 동작의 괴리를 대조한다

문서가 "레포의 X 형식에 맞춰"라고 **서술**하면, X 를 **읽는 단계가 절차에 실제로 있는지** 대조한다. 이슈 #12 의 본질이 이것이었다 — 스킬 첫 줄은 "레포의 PR 템플릿 형식에 맞춰"라고 선언하는데 절차 어디에도 그 파일을 읽는 단계가 없고 본문이 하드코딩돼 있었다. 이 레포엔 `.github/` 템플릿이 없어 개발 중에는 fallback 이 정상 동작으로 보였고, **다른 레포에 설치됐을 때만** 조용히 틀린 본문이 나온다.


## 관련
[[ci-coverage-facts-validate]] · [[harness-plugin-scope-marketplace-sha]]
