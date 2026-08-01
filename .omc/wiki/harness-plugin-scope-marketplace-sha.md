---
title: "harness plugin 용어 — scope · marketplace · 캐시 SHA"
tags: ["plugin", "terminology", "setup", "harness"]
created: 2026-08-01T14:17:24.137Z
updated: 2026-08-01T14:17:24.137Z
sources: []
links: ["pipeline-phase-slug-stage-worktree.md", "docs-vs-omc-wiki.md", "ci-coverage-facts-validate.md", "shell-and-cli-environment-traps-zsh-glob-gh-projects-classic.md"]
category: architecture
confidence: medium
schemaVersion: 1
---

# harness plugin 용어 — scope · marketplace · 캐시 SHA

이 레포는 **레포 = plugin = marketplace** 다 (ADR-002). 그래서 배포 관련 용어가 겹쳐 보인다.

## 정의

| 용어 | 정의 |
| --- | --- |
| **plugin** | `.claude-plugin/plugin.json` 이 선언하는 배포 단위. 이름 `harness`. 스킬은 `skills/` 아래. |
| **marketplace** | `.claude-plugin/marketplace.json`. 이 레포가 자기 자신을 배포처로 광고한다. |
| **scope** | `/harness:setup` 이 묻는 설치 방식. `global` 또는 `project`. `.claude/settings.local.json` 의 `env.HARNESS_SCOPE` 에 저장. |
| **캐시 SHA** | plugin 이 설치되는 경로 `~/.claude/plugins/cache/harness/harness/<sha>/` 의 12자리 hex. **커밋 SHA 가 곧 버전.** |

## global vs project scope

| | `global` | `project` |
| --- | --- | --- |
| `pipeline.py` | plugin 캐시의 번들을 그대로 실행 | 대상 레포 `scripts/pipeline.py` 로 **복사** |
| 업데이트 | `/plugin marketplace update` 로 자동 | 안 됨 → `/harness:setup` 재실행 필요 |
| 복사본 출처 | — | shebang 아래 `# harness plugin <sha> 에서 복사 (<날짜>)` 헤더 2줄 |

어느 복사본이든 **cwd 기준 git root** 에 phase 를 만든다. 즉 실행 위치가 곧 대상 레포다. (`pipeline.py:31-47`)

### project scope 의 fail-closed 조건 (ADR-008)
캐시 경로의 `<sha>` 자리가 **12자리 hex 가 아니면 복사 자체를 거부**한다. plugin 으로 설치된 게 아니라는 뜻이므로, 거짓 출처를 적느니 복사하지 않는다. 로컬 clone·symlink 개발에서는 global scope 만 쓸 수 있다.

## `version` 필드를 일부러 생략한다

`plugin.json` 에 `version` 이 **없다**. 이유는 두 겹이다:

1. 커밋 SHA 가 곧 버전이라 push 즉시 업데이트가 된다 (ADR-002).
2. `version` 을 넣으면 캐시 경로가 `harness/<version>` 이 되어 위 **12자리 hex 검사가 project scope 복사를 거부**한다 (ADR-010). 실측 근거: `ponytail/4.8.4`, `oh-my-claudecode/4.15.7` 캐시 경로.

그 대가로 "무엇이 바뀌었는지 알 방법이 없다"가 생기고, `CHANGELOG.md` 가 그걸 메꾼다. `claude plugin validate` 가 내는 version 경고는 **의도된 것**이다.

## 설정 저장 위치

`.claude/settings.local.json` 의 `env` 키 (ADR-003):

```json
{ "env": { "HARNESS_SCOPE": "global|project", "HARNESS_DOCS_PATH": "docs" } }
```

- `env` 를 쓰는 이유: settings 스키마가 지원하는 키라 unknown-key 경고가 없고, Claude Code 가 세션 환경변수로 주입해 JSON 파싱 없이 읽힌다.
- **이 파일은 gitignore 대상**이라 커밋되지 않는다 → 팀원 각자 `/harness:setup` 을 한 번 실행해야 한다.
- setup 직후 세션 재시작 전에는 env 주입이 안 되므로, 스킬은 환경변수를 먼저 읽고 없으면 파일의 `env` 객체를 직접 읽는다.

plugin 활성화(`enabledPlugins`)도 같은 파일에 넣는다 — 커밋되는 `.claude/settings.json` 에 넣으면 **보안상 무시된다**(레포가 팀원에게 임의 플러그인 설치를 강제하는 걸 막기 위해).

## 대상 레포에 뿌리는 것의 제약

harness 는 **남의 레포에서 도는** plugin 이다. 그래서 뿌리는 것(gitignore 줄·훅·스크립트·CI)은 **대상 레포에 런타임 의존을 만들지 않는다** — 대상의 언어·툴체인을 모르는 게 기본값이다.

`/harness:setup` 이 대상 `.gitignore` 에 넣는 건 두 줄뿐: `.claude/worktrees/`, `.claude/settings.local.json`. `phases/` 는 넣지 않는다(ADR-005). `.omc/` 관련 줄도 넣지 않는다.

따라서 **루트 `CLAUDE.md` 를 고치면 `skills/setup/templates/CLAUDE-section.md` 미러도 같이 고쳐야 하지만**, 대상 레포에 해당하지 않는 규범(예: CHANGELOG 규칙 — 대상은 plugin 이 아니다)은 미러에 넣지 않는다.

## 관련
[[pipeline-phase-slug-stage-worktree]] · [[docs-vs-omc-wiki]] · [[ci-coverage-facts-validate]] · [[shell-and-cli-environment-traps-zsh-glob-gh-projects-classic]]

