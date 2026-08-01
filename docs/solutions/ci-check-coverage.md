---
date: 2026-08-01
track: knowledge
category: best-practices
title: CI 체크는 "통과하는지"가 아니라 "무엇을 덮는지"로 검증한다
tags: [ci, github-actions, claude-plugin, validation, harness]
---

# CI 체크는 "통과하는지"가 아니라 "무엇을 덮는지"로 검증한다

- 날짜: 2026-08-01
- 작업/PR: [#18](https://github.com/seungdeok/harness-starter/pull/18) (이슈 [#15](https://github.com/seungdeok/harness-starter/issues/15)), 브랜치 `CI-VALIDATE`

## 문제

이슈 #15 가 `claude plugin validate .` 를 "version 생략 정책(ADR-002)의 안전망"으로 제안했고, 초기 계획은 그 전제를 그대로 받아 **validate 하나만** 넣는 범위로 잡혔다.

이름과 이슈 설명만 보면 "플러그인을 검증한다"고 읽히지만, 실제 커버리지를 아무도 확인하지 않은 상태였다.

## 원인

**검사 도구의 커버리지를 실측하지 않고 이름으로 추정했다.**

temp 레포에 프론트매터가 아예 없는 `skills/broken/SKILL.md` 를 넣고 돌려보니:

```
✔ Validation passed with warnings
exit=0
```

`claude plugin validate` 는 `.claude-plugin/*.json`(marketplace.json, plugin.json)만 검사한다. `skills/**/SKILL.md` 는 쳐다보지 않는다.

그런데 이 레포에서 실제로 자주 바뀌는 건 `pipeline.py`(7회)·`skills/pipeline/SKILL.md`(4회)고, manifest 는 거의 안 바뀐다. **validate 단독은 가장 안 깨지는 파일을 지키는 셈**이었다 — 게이트로서 유효하긴 하나 "안전망"이라 부르기엔 얇았다.

## 해결

1. plan-eng-review 단계에서 위 실측 결과를 근거로 범위를 재조정 → 이슈 원안대로 `pipeline.py selftest` 를 한 줄 추가.
2. 게이트가 **실제로 실패하는지** 양방향으로 확인:

   | 케이스 | 결과 |
   | --- | --- |
   | 정상 | `selftest OK` exit 0 / `Validation passed` exit 0 |
   | `pipeline.py` 의 stage 이름 하나 변경 | `AssertionError` **exit 1** |
   | `marketplace.json` JSON 파손 | `Validation failed` **exit 1** |

3. 원격 실행 가능성도 실측: 빈 `HOME`·API 키 없이 `env -i` 로 돌려 통과 → CI 러너에 인증 불필요.

최종 workflow (`.github/workflows/validate.yml`) — 실제 CI pass, 10초.

## 재발 방지

CI 체크를 추가할 때 두 가지를 실측한다:

1. **음성 케이스**: 일부러 깨뜨려서 `exit 1` 이 나오는지. 통과만 확인한 체크는 "항상 초록불"인지 "실제로 막는지" 구분이 안 된다.
2. **커버리지 대조**: 그 체크가 덮는 파일이, `git log` 상 실제로 자주 바뀌는 파일과 겹치는지. 안 바뀌는 파일만 덮는 체크는 안전망이 아니다.

→ GUARDRAILS.md 에 승격.

## 부수 교훈 — `gh` 서브커맨드의 Projects classic 에러

`gh issue view` / `gh pr edit` 가 이 레포에서 아래 에러로 실패했다 (두 번 발생):

```
GraphQL: Projects (classic) is being deprecated ... (repository.issue.projectCards)
```

서브커맨드가 응답에 projectCards 를 같이 요청해서 나는 에러라 인자로는 못 피한다. `gh api` 로 우회한다:

```bash
gh api repos/<owner>/<repo>/issues/15 --jq '{number,title,body}'
gh api repos/<owner>/<repo>/pulls/18 -X PATCH -F body=@body.md
```

`gh pr create` / `gh pr checks` / `gh api` 는 정상 동작한다.
