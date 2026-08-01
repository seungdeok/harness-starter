---
title: "pipeline 용어 — phase · slug · stage · worktree"
tags: ["pipeline", "terminology", "harness"]
created: 2026-08-01T14:16:25.309Z
updated: 2026-08-01T14:16:25.309Z
sources: []
links: ["compound-engineering.md", "docs-vs-omc-wiki.md", "harness-plugin-scope-marketplace-sha.md", "worktree-phase-traps-cwd.md", "git-diff-scope-and-merge-conflict-precheck-pr.md"]
category: reference
confidence: medium
schemaVersion: 1
---

# pipeline 용어 — phase · slug · stage · worktree

`/harness:pipeline` 과 `skills/pipeline/scripts/pipeline.py` 에서 쓰는 용어의 정의와 구분.

## 정의

| 용어 | 정의 | 근거 |
| --- | --- | --- |
| **phase** | 파이프라인이 한 번에 굴리는 **작업 단위 하나**. `phases/<slug>/phase.json` 이 그 상태를 들고 있다. | `pipeline.py:48` `PHASES = ROOT / "phases"` |
| **slug** | phase 이름을 정규화한 문자열. 소문자화 후 영숫자·한글·하이픈 외 문자를 `-` 로 치환하고 중복 하이픈을 접는다. | `pipeline.py:95-97` `_slug()` |
| **branch** | slug 를 **그대로 대문자로** 한 것. `feat-` 같은 접두어를 붙이지 않는다. | `pipeline.py:101-102` `_branch()`, ADR-001 |
| **stage** | phase 안의 순서 있는 단계. `discuss → plan → [ceo] → [eng] → approve → implement → verify → commit-push → make-pr → compound` | `pipeline.py:55-66` `STAGES` |
| **worktree** | phase 전용 격리 체크아웃. `<메인루트>/.claude/worktrees/<slug>` 고정. | `pipeline.py:132-134` `_wt_path()` |

예: 이름 `"omc wiki gitignore"` → slug `omc-wiki-gitignore` → branch `OMC-WIKI-GITIGNORE` → worktree `.claude/worktrees/omc-wiki-gitignore`

## 구분이 헷갈리는 것들

### phase vs stage
**phase 는 작업, stage 는 그 작업의 단계**다. phase 는 여러 개가 동시에 살아 있을 수 있고(각자 worktree/브랜치), stage 는 한 phase 안에서 항상 하나만 활성이다. `status`/`advance` 는 활성 phase 가 하나면 인자 없이 자동 인식하고, 여러 개면 이름을 줘야 한다.

### STAGES vs TDD_PAIR
`TDD_PAIR`(`implement-red` / `implement-green`)는 `STAGES` **상수에 들어 있지 않다**. doc-build 시점에 `implement` 자리에 splice 된다. 그래서 `STAGES` 만 읽으면 TDD 단계가 안 보인다. (`pipeline.py:75-80`, ADR-004)

### 선택 stage 3종
| 분류 | 대상 | 생략 방법 |
| --- | --- | --- |
| `REVIEW_STAGES` | `plan-review-ceo`, `plan-review-eng` | `init --no-review` |
| `COMPOUND_STAGE` | `compound` | `init --no-compound` (SKILL 은 **항상** 이걸 붙인다) |
| TDD splice | `implement-red/green` | `init --no-tdd` |

### INTERACTIVE_STAGES 는 생략 불가
`discuss` 와 `approve` 는 "사람과의 대화가 곧 실행"이라 headless 로 못 돈다. opt-out 플래그가 없다 — 계획 승인이 파이프라인의 존재 이유이기 때문. (`pipeline.py:70`, ADR-004)

### ROOT vs _main_root()
| | 값 | 쓰임 |
| --- | --- | --- |
| `ROOT` | **cwd 기준** git root (worktree 안이면 worktree root) | `phases/` 위치, 대부분의 git 실행 |
| `_main_root()` | `git rev-parse --git-common-dir` 의 부모 = **메인 체크아웃** | worktree 경로 계산, `done` 이 자기 worktree 를 지울 때 |

`ROOT` 는 git 밖이면 **fail-closed 로 죽는다**(`sys.exit`). cwd 폴백을 없앤 이유는 서브에이전트 cwd 가 다를 때 조용히 엉뚱한 레포에 `phases/` 를 만드는 걸 막기 위해서다. (`pipeline.py:31-47`, ADR-009)

### phase.json vs plan.md
| | 역할 | 커밋 |
| --- | --- | --- |
| `phases/<slug>/phase.json` | 지금 몇 번째 stage 인지 기억하는 **상태 파일**. 중간에 끊겨도 이어서 진행 가능. | ✗ |
| `phases/<slug>/plan.md` | `approve` 가 승인받고 `verify` 가 기준으로 삼는 **문서** | ✗ |

`phases/` 는 **전부** 커밋 대상이 아니고, `.gitignore` 규칙도 두지 않는다 — 그래서 `git status` 에 항상 untracked 로 뜬다. 의도된 상태다. `git add .` 로 쓸어 담지 말 것. (CLAUDE.md §6, ADR-005)

plan.md 가 PR diff 에 안 보이므로 **PR 본문에 계획 요약을 넣는 것**으로 대체한다.

## 관련
[[compound-engineering]] · [[docs-vs-omc-wiki]] · [[harness-plugin-scope-marketplace-sha]] · [[worktree-phase-traps-cwd]] · [[git-diff-scope-and-merge-conflict-precheck-pr]]

