# worktree phase 의 pipeline.py 명령은 매번 cd 를 붙인다 — cwd 가 곧 어느 phase 인지다

- 날짜: 2026-08-01
- 작업/PR: [#21](https://github.com/seungdeok/harness-starter/pull/21) (이슈 [#13](https://github.com/seungdeok/harness-starter/issues/13)), 브랜치 `SKILL-PRECHECK`

## 문제

전용 worktree 로 phase 를 돌리는 중, `pipeline.py advance` 를 `cd` 없이 실행했다.
`discuss` 는 `cd <worktree> && python3 ...` 로 실행했지만 다음 `plan` advance 에서 `cd` 를 빼먹었다.

결과적으로는 맞는 phase 가 advance 됐다 — 세션의 Bash cwd 가 명령 간 유지돼서 앞선 `cd` 가 아직 살아 있었기 때문이다.
**의도해서 맞은 게 아니라 우연히 맞았다.**

## 원인

`pipeline.py` 의 phase 탐색은 스크립트 위치가 아니라 **cwd 기준 git root** 다 (ADR-002 에서 의도적으로 그렇게 바꿨다):

```python
ROOT = _git_root()      # cwd 기준 git rev-parse --show-toplevel
PHASES = ROOT / "phases"
```

그래서 같은 `advance` 명령이 **어디서 실행되느냐에 따라 다른 phase 를 건드린다.**
worktree 안이면 worktree 의 `phases/`, 메인 체크아웃이면 메인의 `phases/` 다.

여기에 `_resolve(None)` 의 동작이 겹친다:

```python
active = [f for f in PHASES.glob("*/phase.json") if 진행중]
if not active:        sys.exit("진행 중인 phase 가 없어요")
if len(active) > 1:   sys.exit("여러 개예요 — 이름을 지정하세요")
return active[0]      # ← 정확히 하나면 확인 없이 그걸 쓴다
```

활성 phase 가 **정확히 하나**면 아무것도 묻지 않는다. 메인 레포에 다른 활성 phase 가 하나 있는 상태에서
worktree phase 를 advance 하려고 `cd` 를 빼먹으면, 에러 없이 **엉뚱한 phase 가 조용히 advance 된다.**
이번엔 메인의 유일한 phase(`settings-local-json`)가 이미 완료 상태(`cursor=6/6`)라 걸리지 않았을 뿐이다.

"아까 cd 했으니 지금도 거기겠지"는 검증이 아니다. 셸 cwd 는 보이지 않는 상태고,
중간에 다른 목적으로 `cd` 한 명령이 하나만 끼어도 뒤집힌다 (이 세션에서도 실제로 한 번 끼었다).

## 해결

worktree 로 돌리는 phase 는 **모든** `status`/`advance` 에 `cd` 를 붙여 한 줄로 실행한다:

```bash
cd /path/to/.claude/worktrees/<slug> && python3 <pipeline.py> advance --summary "..."
```

`pipeline.py` 는 이미 init 출력에서 이걸 안내하고 있다 — 안내가 없어서가 아니라 지키다 만 게 문제였다.

```
이후 명령은 worktree 안에서 실행하세요: cd .../.claude/worktrees/<slug>
```

phase 가 여러 개일 땐 인자로 이름을 주는 것도 방법이지만(`advance <slug>`), 이름은 worktree 밖에서 주면
**메인의 동명 phase** 를 찾으므로 `cd` 를 대체하지 못한다. cwd 가 1차 방어다.

## 재발 방지

- worktree phase 명령은 `cd <worktree> && ...` 를 한 줄에 묶는다. 앞 명령의 cwd 에 기대지 않는다.
- 이상하면 `advance` 전에 `python3 <pipeline.py> status` 를 먼저 찍어 phase 이름과 stage 번호를 눈으로 확인한다.

관련: 이번 작업의 설계 결정(스킬 점검을 코드가 아닌 지침으로)은 `docs/ADR.md` ADR-007 에 있다.
