---
title: "CI coverage facts — validate 가 덮는 것과 안 덮는 것"
tags: ["ci", "github-actions", "validation", "harness"]
created: 2026-08-01T14:26:30.542Z
updated: 2026-08-01T14:26:30.542Z
sources: []
links: ["shell-and-cli-environment-traps-zsh-glob-gh-projects-classic.md", "harness-plugin-scope-marketplace-sha.md", "compound-engineering.md"]
category: architecture
confidence: medium
schemaVersion: 1
---

# CI coverage facts — validate 가 덮는 것과 안 덮는 것

이 레포 CI 의 실측 커버리지. 근거: `docs/solutions/ci-check-coverage.md` (PR #18), ADR-010

## `claude plugin validate` 는 매니페스트만 본다

temp 레포에 **프론트매터가 아예 없는** `skills/broken/SKILL.md` 를 넣고 돌린 결과:

```
✔ Validation passed with warnings
exit=0
```

즉 `.claude-plugin/*.json`(`plugin.json`, `marketplace.json`)만 검사하고 **`skills/**/SKILL.md` 는 쳐다보지 않는다.**

이게 왜 중요하냐면, 이 레포에서 실제로 자주 바뀌는 건 `pipeline.py`(7회)·`skills/pipeline/SKILL.md`(4회)고 매니페스트는 거의 안 바뀐다. **validate 단독은 가장 안 깨지는 파일을 지키는 셈**이라 게이트로는 유효해도 "안전망"이라 부르기엔 얇다. 그래서 `pipeline.py selftest` 를 함께 둔다.

## 워크플로우 2개로 분리돼 있다 (ADR-010)

| 워크플로우 | 내용 | 트리거 |
| --- | --- | --- |
| `validate.yml` | `pipeline.py selftest` | **모든 PR** |
| `plugin-validate.yml` | `claude plugin validate` | `paths: ['.claude-plugin/**']` |

분리한 이유: unpinned `npm i -g` 로 설치하는 CLI 가 매니페스트와 **무관한 PR** 을 빨갛게 만들었다. `paths` 필터는 그 비용만 없애고 게이트는 남긴다. 부수 효과로 unpinned 설치 빈도가 "모든 PR"에서 "매니페스트 변경 시"로 떨어져 공급망 노출도 준다.

### `paths` 필터의 침묵 실패 주의
워크플로우가 영영 안 도는데 **"체크가 안 보이는 것"이 이 설계에선 정상 동작**이라 구분이 안 된다. 매칭을 실측하면 위험한 오타는 `*`/`**` 가 아니라 **디렉토리명**이다:

| 패턴 | 매칭 |
| --- | --- |
| `.claude-plugin/**` | 2/2 |
| `.claude-plugin/*` | 2/2 (평평한 디렉토리라 동일) |
| `.claude-plugins/**` · `claude-plugin/**` | **0/2 — 조용히 통과** |

`**` 를 택한 건 나중에 하위 디렉토리가 생겨도 계속 잡히게 하려는 것. 매니페스트를 바꾼 PR 에서 `plugin-validate` 가 **실제로 뜨는지** 확인하는 게 도입 시 필수 절차다.

## 게이트가 실제로 막는지 양방향 실증 기록

| 케이스 | 결과 |
| --- | --- |
| 정상 | `selftest OK` exit 0 / `Validation passed` exit 0 |
| `pipeline.py` 의 stage 이름 하나 변경 | `AssertionError` **exit 1** |
| `marketplace.json` JSON 파손 | `Validation failed` **exit 1** |

**통과만 확인한 체크는 "항상 초록불"인지 "실제로 막는지" 구분이 안 된다.** CI 체크를 추가하면 일부러 깨뜨려 본다.

## CI 러너에 인증이 필요 없다

빈 `HOME`·API 키 없이 `env -i` 로 돌려 통과함을 실측. 전체 워크플로우 약 10초.


## 관련
[[shell-and-cli-environment-traps-zsh-glob-gh-projects-classic]] · [[harness-plugin-scope-marketplace-sha]] · [[compound-engineering]]
