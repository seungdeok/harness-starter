---
title: "worktree phase traps — cwd 침묵 실패와 정리 사고"
tags: ["worktree", "pipeline", "cwd", "cleanup", "harness"]
created: 2026-08-01T14:27:04.368Z
updated: 2026-08-01T14:27:04.368Z
sources: []
links: ["pipeline-phase-slug-stage-worktree.md", "git-diff-scope-and-merge-conflict-precheck-pr.md", "omc-gitignore-layers.md"]
category: debugging
confidence: medium
schemaVersion: 1
---

# worktree phase traps — cwd 침묵 실패와 정리 사고

전용 worktree 로 phase 를 돌릴 때 **조용히** 잘못되는 두 가지. 근거: `docs/solutions/pipeline-worktree-cwd.md` (PR #21), `docs/solutions/probe-constraints-before-planning.md` (PR #22)

## 1. cwd 를 놓치면 엉뚱한 phase 가 advance 된다

`pipeline.py` 의 phase 탐색은 스크립트 위치가 아니라 **cwd 기준 git root** 다 (ADR-002 에서 의도적으로 그렇게 바꿨다).

```python
ROOT = _git_root()      # cwd 기준 git rev-parse --show-toplevel
PHASES = ROOT / "phases"
```

같은 `advance` 명령이 **어디서 실행되느냐에 따라 다른 phase 를 건드린다.** 여기에 `_resolve(None)` 의 동작이 겹친다:

```python
active = [f for f in PHASES.glob("*/phase.json") if 진행중]
if not active:        sys.exit("진행 중인 phase 가 없어요")
if len(active) > 1:   sys.exit("여러 개예요 — 이름을 지정하세요")
return active[0]      # ← 정확히 하나면 확인 없이 그걸 쓴다
```

활성 phase 가 **정확히 하나면 아무것도 묻지 않는다.** 메인 레포에 다른 활성 phase 가 하나 있는 상태에서 worktree phase 를 advance 하려고 `cd` 를 빼먹으면, **에러 없이 엉뚱한 phase 가 조용히 advance 된다.**

실제로 한 번 빼먹었는데 맞는 phase 가 advance 됐다 — 세션 Bash cwd 가 명령 간 유지돼서 앞선 `cd` 가 살아 있었기 때문이다. **의도해서 맞은 게 아니라 우연히 맞았다.**

### 대응
모든 `status`/`advance` 를 `cd` 와 한 줄로 묶는다.

```bash
cd /path/to/.claude/worktrees/<slug> && python3 <pipeline.py> advance --summary "..."
```

- "아까 `cd` 했으니 지금도 거기겠지"는 검증이 아니다. 셸 cwd 는 **보이지 않는 상태**고, 다른 목적으로 `cd` 한 명령이 하나만 끼어도 뒤집힌다.
- 이름 인자(`advance <slug>`)는 `cd` 를 **대체하지 못한다** — worktree 밖에서 주면 메인의 동명 phase 를 찾는다. cwd 가 1차 방어다.
- 이상하면 `advance` 전에 `status` 를 먼저 찍어 phase 이름과 stage 번호를 눈으로 확인한다.

## 2. worktree 의 `.claude/` 에는 추적 파일이 들어 있다

probe 로 만든 중첩 디렉토리를 정리하면서 부모인 `<worktree>/.claude` 를 통째로 `rmtree` 했더니, 같이 있던 **추적 파일 4,600여 줄**이 날아갔다 — `.claude/settings.json`, `.claude/skills/plan-ceo-review/**`, `.claude/skills/plan-eng-review/**`.

`git status` 에서 대량 삭제로 잡혀 `git checkout -- .claude/` 로 복구했지만, **커밋 직전에 diff 를 안 봤으면 그대로 PR 에 실렸다.** 원인은 단순하다: 지우려던 건 자식 하나인데 부모 디렉토리를 지웠다.

### 대응
- probe·임시 산출물은 **만든 것만** 지운다. 부모 디렉토리 `rmtree`/`rm -rf` 금지.
- 지운 뒤 `git status` 로 **예상 밖 삭제가 없는지** 확인한다.

## 3. worktree 제거는 기본 경로가 항상 실패한다

**모든** phase worktree 는 `phases/<slug>/`(untracked, ADR-005)를 갖고 있다. 그래서 `git worktree remove` 를 그냥 부르면:

```
fatal: ... contains modified or untracked files, use --force
```

`--force` 를 기본으로 붙이는 건 커밋 안 한 실제 작업을 조용히 날리는 경로다. 그래서 `pipeline.py done` 은 `phases/` 를 먼저 지우되, 그 전에 `git status --porcelain` 으로 확인해 **`phases/` 외 변경이 있으면 아무것도 지우지 않는다.**

## 4. `init` 과 `done` 의 기준점이 갈라졌던 버그

`cmd_init` 이 `ROOT`(현재 체크아웃) 기준으로 worktree 를 만드는데 `cmd_done` 은 메인 체크아웃 기준으로 찾았다. worktree **안에서** `init` 하면 `<worktree>/.claude/worktrees/` 에 중첩 생성돼 `done` 이 영원히 못 찾는다.

경로 규칙을 `_wt_path()` 로 공유했는데도 **기준점(base)이 갈라져 있어서** 공유가 무의미했다. 지금은 둘 다 `_main_root()` 기준으로 통일돼 있다. 코드를 읽어서는 안 보이고 **돌려봐야 보이는** 종류의 결함이었다.


## 관련
[[pipeline-phase-slug-stage-worktree]] · [[git-diff-scope-and-merge-conflict-precheck-pr]] · [[omc-gitignore-layers]]
