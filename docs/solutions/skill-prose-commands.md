---
date: 2026-08-01
track: knowledge
category: best-practices
title: 스킬 문서에 적은 셸 명령은 검증되지 않은 코드다 — 두 상태로 실행해 본다
tags: [skill, prompt, shell, zsh, gh-cli, verification, harness]
---

# 스킬 문서에 적은 셸 명령은 검증되지 않은 코드다 — 두 상태로 실행해 본다

- 날짜: 2026-08-01
- 작업/PR: [#20](https://github.com/seungdeok/harness-starter/pull/20) (이슈 [#12](https://github.com/seungdeok/harness-starter/issues/12)), 브랜치 `READ-REPO-TEMPLATES`

## 문제

이슈 #12 는 `make-pr`·`make-issue` 가 "레포 템플릿 형식에 맞춰" 만든다고 서술하면서 실제로 템플릿 파일을 읽는 단계가 없다는 버그였다. 고치려면 SKILL.md 에 탐색 명령을 써 넣으면 되는 일이라, 마크다운 문서 수정으로만 끝나는 작업처럼 보였다.

그런데 **작성한 명령 두 개가 실제로는 실패하는 명령이었다.** 문서만 읽어서는 둘 다 멀쩡해 보인다.

## 원인

**SKILL.md 안의 셸 명령은 실행되는 코드인데, 산문 안에 있다는 이유로 아무도 실행해 보지 않는다.** 스킬은 테스트 스위트가 없고 CI(`claude plugin validate`)도 `SKILL.md` 본문은 쳐다보지 않으므로(→ [ci-check-coverage.md](ci-check-coverage.md)), 여기 적힌 명령은 사실상 검증되지 않은 코드로 배포된다.

두 결함 모두 **실행해서만** 드러났다:

**1. zsh 의 glob nomatch 는 `2>/dev/null` 을 뚫는다**

```bash
ls .github/ISSUE_TEMPLATE/*.md 2>/dev/null
# zsh: (eval):4: no matches found: .github/ISSUE_TEMPLATE/*.md
```

매칭이 없을 때 에러를 내는 주체가 `ls` 가 아니라 **셸**이다. 리다이렉션은 `ls` 의 stderr 에만 걸리므로 셸의 nomatch 에러는 그대로 새어 나온다. bash 에서는 glob 이 그대로 넘어가 `ls` 가 조용히 실패하니 문제가 안 보이고, zsh 에서만 터진다.

**2. `gh label list --json` 은 설치된 버전에 없다**

```bash
gh label list --help   # gh 2.7.0
# FLAGS
#   -L, --limit int   Maximum number of items to fetch (default 30)
#   -w, --web         List labels in the web browser
```

`--json` 은 최신 `gh` 문서에는 있지만 2.7.0 에는 없다. 기억이나 상위 버전 문서를 근거로 쓴 플래그였다.

## 해결

**탐색 명령을 `find` 로 통일** — `find` 는 셸 glob 을 쓰지 않으므로 nomatch 문제 자체가 없다:

```bash
find .github docs . -maxdepth 1 -iname 'pull_request_template.md' 2>/dev/null
find .github/PULL_REQUEST_TEMPLATE -name '*.md' 2>/dev/null
```

**라벨 조회를 버전 무관한 형태로** — `--json` 대신 기본 출력에서 이름 열만 뽑는다:

```bash
gh label list --limit 100 | cut -f1
```

**두 상태로 실행해 검증** — 이게 결함을 잡아낸 절차 자체다:

| 상태 | 기대 | 실제 |
| --- | --- | --- |
| 템플릿 없음 (이 레포) | 에러 없이 빈 결과 → fallback | ✅ (수정 전에는 nomatch 에러) |
| 템플릿 있음 (임시 scaffold) | 4개 경로 모두 검출 | ✅ |
| 라벨 조회 | 라벨 이름 목록 | ✅ (수정 전에는 unknown flag) |

임시 scaffold 는 레포를 건드리지 않게 `$TMPDIR` 에 만들어 돌렸다.

## 재발 방지

스킬·문서·플레이북에 셸 명령을 써 넣을 때:

1. **결과 있음 / 결과 없음 두 상태로 실제 실행한다.** "찾으면 A, 없으면 B" 분기를 적었다면 두 경로 모두 밟아 본다. 대부분의 결함은 **없음** 쪽에 숨어 있다 — 성공 경로만 확인하면 안 보인다.
2. **glob 을 조건부 조회에 쓰지 않는다.** 매칭이 없을 수 있는 자리에는 `ls *.ext` 대신 `find <dir> -name '*.ext'` 를 쓴다. zsh 에서 nomatch 는 `2>/dev/null` 로 못 막는다.
3. **CLI 플래그는 `--help` 로 설치된 버전에 있는지 확인한다.** 공식 문서에 있어도 사용자 환경의 구버전에는 없을 수 있다. 스킬은 남의 환경에서 도는 코드다.

→ GUARDRAILS.md 에 승격.

## 부수 교훈 — "X 형식에 맞춰"라는 서술은 X 를 읽는 단계와 대조한다

이슈 #12 의 본질은 **서술과 동작의 괴리**였다. 스킬 첫 줄은 "레포의 PR 템플릿 형식에 맞춰"라고 선언하는데, 절차 어디에도 그 파일을 읽는 단계가 없고 본문 구조는 하드코딩되어 있었다.

이 레포에는 `.github/` 템플릿이 아예 없어서 개발 중에는 fallback 이 곧 정상 동작으로 보였고, **다른 레포에 설치됐을 때만** 조용히 틀린 본문이 나온다. plugin 처럼 남의 레포에서 도는 코드는 "우리 레포에서 잘 된다"가 검증이 아니다.

문서가 외부 파일·설정·규약을 따른다고 서술하면, 그것을 **읽는 단계가 절차에 실제로 있는지** 대조한다.
