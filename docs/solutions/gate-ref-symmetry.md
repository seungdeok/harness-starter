# 게이트는 "무엇을 봤는가"가 아니라 "무엇을 보증하는가"로 읽는다 — 비교식 양변의 ref 종류

- 날짜: 2026-08-02
- 작업/PR: [#33](https://github.com/seungdeok/harness-starter/pull/33) (이슈 [#32](https://github.com/seungdeok/harness-starter/issues/32)), 브랜치 `COMPOUND-GATE-REMOTE`

## 문제

`pipeline.py done` 의 compound 게이트(ADR-009)는 worktree 를 지우기 전에 "이 작업이 교훈을 남겼는가"를
확인하게 돼 있었다. 판정은 이 한 줄이었다.

```python
r = _run_git("diff", "--name-only", f"origin/{base}...{branch}", cwd=main)
```

2026-08-01 phase `omc-wiki-gitignore` 에서 게이트는 **통과**했고 `✓ 정리 완료` 를 찍었다.
그런데 그 시점에 교훈은 **로컬 브랜치에만** 있었다 — push 도, 머지도 안 된 채로.

## 원인

비교식의 **양변이 다른 네임스페이스**였다. 좌변 `origin/{base}` 는 원격 ref, 우변 `{branch}` 는 **로컬 ref**.
그래서 이 식이 실제로 답하는 질문은 이랬다.

| 물었다고 믿은 것 | 실제로 물은 것 |
| --- | --- |
| 교훈이 안전하게 기록됐는가 | 로컬 브랜치에 그런 파일을 만진 커밋이 있는가 |

로컬에만 있는 커밋은 두 번째 질문에 당연히 "예"라고 답한다. **게이트가 막으려던 상황이 정확히 그 상태인데도.**

### 커밋이 안 날아간 건 게이트 덕분이 아니었다

`done` 은 worktree 를 지웠지만 `git branch -d` 는 `not fully merged` 로 거부해서 커밋이 살아남았다.
게이트가 작동한 것처럼 보인 이유다. 실제 이유는 다르다 — **PR 이 squash 로 머지돼서** 브랜치 tip 이
`main` 의 조상이 아니었을 뿐이다. rebase 머지였다면 `-d` 가 조용히 성공했을 것이고, 실제로 그다음 수순인
`git branch -D` 를 사람이 눌렀으면 그대로 사라졌다(이번엔 직전에 발견해 cherry-pick 으로 구조했다).

**보호의 근거가 "compound 가 안 올라갔다"가 아니라 "머지 방식이 squash 였다"인 것은 안전장치가 아니다.**

### 왜 push 만으로도 부족했나

파이프라인 stage 는 `... → commit-push → make-pr` 이고 compound 는 그 **밖**에 있다(ADR-001).
그래서 `/ce-compound` 는 구조적으로 PR 이 머지된 **뒤에** 돈다 — push 를 유도하는 stage 가 이미 지나갔고,
push 했어도 `main` 에 넣으려면 새 PR 이 필요하다. 게이트의 검사 시점과 stage 순서가 어긋나 있었다.

## 해결

질문을 "건드렸는가"에서 **"교훈이 `origin/<base>` 에 도착했는가"** 로 바꾸고 두 단계로 나눴다.

```python
base = _base_branch(main)
_run_git("fetch", "--quiet", "origin", base, cwd=main)      # 로컬 origin/<base> 가 낡으면 오탐
changed = _branch_changed_files(main, base, branch)          # 3-dot: 귀속
notes = _solution_notes(changed, docs)                       # <docs>/solutions/ 만
if not notes:   sys.exit("compound 미수행 ...")
# two-dot: 내용이 base 에 도착했는가
if not any(_arrived(main, base, branch, p) for p in notes):
    sys.exit(f"교훈이 origin/{base} 에 없어요 ...")
```

**three-dot 은 귀속, two-dot 은 도착.** 각각 다른 질문이라 둘 다 필요하다.

- `origin/base...branch` (3-dot) — merge-base 이후 이 브랜치가 바꾼 것. **남의 노트를 통과시키지 않는다.**
- `origin/base branch -- <file>` (2-dot) — 두 tip 의 내용 비교. 도달 가능성이 아니라 **내용**을 물으므로
  squash·rebase·cherry-pick·별도 PR 어느 경로로 머지돼도 같은 답이 나온다.

### 검증은 구버전을 같은 케이스에 돌려서 했다

임시 레포에서 세 상태를 만들고 신·구 양쪽을 돌렸다.

| 케이스 | 구버전 `65bd396` | 새 버전 |
| --- | --- | --- |
| A. PR 머지 후 compound 가 로컬에만 (**사고 재현**) | `✓ 정리 완료` **exit 0** | `ERROR: 교훈이 origin/main 에 없어요` **exit 1** |
| B. 도착 + base 가 남의 노트로 전진 | 통과 | 통과 |
| C. compound 미수행 | 차단 | 차단 |

구버전이 케이스 A 에서 **이슈가 보고한 증상을 그대로 재현**한 것이 이 테스트가 대상 코드 경로를
판별한다는 증거다. 새 버전만 돌려 "차단됐다"를 보는 것으로는 그걸 알 수 없다
([verification-trigger-coverage.md](verification-trigger-coverage.md) 의 역방향 확인).

### 같은 제안의 두 버전 — 로컬 git 은 기각, GitHub API 는 채택

리뷰 중에 더 실용적인 안이 나왔다. solutions 경로만 보지 말고 **모든 작업**을 지키자는 것이다.
같은 아이디어인데 **누구에게 묻느냐**에 따라 하나는 무너지고 하나는 정확했다.

```
1) 병합됐나?      git diff --quiet origin/<base> <branch>   → exit 0 이면 통과
2) 아니면 로컬 커밋? git log origin/<base>..<branch>          → 있으면 차단
```

방향은 맞지만 **squash 머지 앞에서 무너진다.** 실측 결과:

| 케이스 | 실제 상태 | 1) 병합? | 2) 로컬 커밋 | 판정 |
| --- | --- | --- | --- | --- |
| A | compound 가 **로컬에만** (위험) | exit 1 | 2개 | 차단 ✓ |
| **B** | **전부 머지됨** (안전) | **exit 1** | **2개** | **차단 ✗** |
| C | 머지됨, compound 없음 | exit 0 | — | 통과 (compound 누락 못 잡음) |

**A 와 B 가 두 신호 모두 동일하다.**

- 1단계: 내 PR 머지 뒤 남이 뭔가를 올리면 base 트리가 달라져 "미병합"으로 읽힌다. base 전진은 정상이다.
- 2단계: squash 는 새 커밋을 만들어 브랜치 tip 이 `main` 의 조상이 아니다. `origin/main..BRANCH` 는
  **이미 머지된 커밋을 영원히 보여준다** — `git branch -d` 가 거부하는 것과 같은 이유.

`git cherry` 도 안 된다: patch-id 비교라 rebase·cherry-pick 은 잡아내지만, 커밋 여러 개를 하나로
합치는 squash 는 patch-id 가 달라져 전부 `+` 로 나온다.

**로컬 git 만으로는 squash 머지 레포에서 "머지됐나"에 답할 수 없다.**

#### 채택 — 같은 질문을 GitHub 에 묻는다

로컬 git 이 못 하는 이유는 정보가 없어서다. squash 는 원본 커밋과의 연결을 **끊어 버리고**, 그
연결을 아는 건 머지를 수행한 쪽, 즉 GitHub 이다. 그래서 물을 상대를 바꿨다.

```python
gh pr list --head <branch> --state all --limit 1 --json state,commits
```

```
PR 없음 / gh 없음 / 비-GitHub / 오프라인 → None → 내용 비교로 폴백
state != MERGED                        → 차단 "PR 이 아직 머지 안 됐어요"
로컬 tip ∉ PR 커밋 SHA 목록              → 차단 "머지 뒤에 붙은 커밋이 있어요"
그 외                                   → 통과
```

실제 사고 데이터로 검증했다 (`gh` 2.7.0).

| 입력 | 결과 |
| --- | --- |
| PR #33 (진행 중) | 차단: PR 미머지 (state=OPEN) |
| **PR #30 (MERGED) + 머지 뒤 붙은 `d5268b5`** | **차단: tip `d5268b5` ∉ PR `['53c68df']`** ← 사고 재현 |
| PR #30, tip 이 PR 커밋과 동일 | 통과 |
| PR 없는 브랜치 | None → 폴백 |

두 번째 줄이 핵심이다. **squash·rebase·base 전진 전부 무관하고, `docs/solutions/` 밖 작업도
똑같이 지킨다** — 내용 비교로는 `GUARDRAILS.md` 같은 공유 파일 때문에 못 하던 것이다.
`git branch -d` 가 도달 가능성으로 답을 못 낸 바로 그 질문에 SHA 하나 비교로 답한다.

내용 비교(`_arrived`)는 폴백으로 남긴다. `gh` 미설치·미인증, 비-GitHub 레포, 오프라인,
PR 없는 브랜치에서 여전히 돌아야 하기 때문이다 — harness 는 남의 레포에 설치되는 plugin 이고,
`gh` 를 하드 의존으로 만들면 GUARDRAILS 의 *"대상 레포에 런타임 의존을 만들지 않는다"* 를 깬다.
경로가 둘이라 코드가 줄지 않는 건 인정된 비용이다.

## 재발 방지

- **ref 를 비교하는 식은 양변이 같은 네임스페이스인지 본다.** `origin/X...Y` 처럼 한쪽만 원격이면
  그 식은 "원격에 있는가"를 보증하지 않는다. 로컬/원격이 섞이면 조용히 약한 질문이 된다.
- **안전장치가 통과했을 때, 막아 준 근거가 설계인지 우연인지 구분한다.** "사고가 안 났다"는 게이트가
  작동했다는 증거가 아니다. 이번엔 squash 머지라는 무관한 사실이 뒤에서 받쳐 주고 있었다.
- 게이트를 읽을 때 **"이 명령이 무엇을 봤는가"가 아니라 "이 통과가 무엇을 보증하는가"** 로 옮겨 적어 본다.
  두 문장이 다르면 그 차이가 곧 구멍이다.
- **squash 머지를 쓰는 레포에서는 도달 가능성(`branch -d`·`log A..B`·`cherry`)으로 "머지됐나"를 판정하지 않는다.**
  전부 "미머지"라고 답한다.
- **로컬 도구가 답 못 하는 질문은, 그 정보를 실제로 가진 상위 시스템(PR·CI·레지스트리)에 물을 수 있는지 먼저 본다.**
  squash 는 커밋 연결을 끊지만 그 연결을 아는 쪽은 머지를 수행한 GitHub 이다. 로컬 휴리스틱을 정교하게
  깎는 것보다 물을 상대를 바꾸는 게 정확하다 — 대신 그 시스템에 못 닿을 때의 폴백은 설계에 포함한다.

→ [GUARDRAILS.md](GUARDRAILS.md) 에 승격.

## 부수 교훈 1 — 순수 함수 추출은 로직이 있는 곳에서만

계획 단계에서 게이트 판정을 `_gate_verdict(changed, arrived, docs_path) -> str` 이라는 순수 함수로
뽑아 `selftest` 로 덮으려 했다. Eng 리뷰에서 걷어냈다.

그 함수 안에 남는 건 `if not changed / elif not arrived / else` 3분기뿐이고, **진짜 로직**
(경로 prefix 매칭, two-dot 비교)은 전부 바깥에 있다. 테스트는 6개가 늘지만 덮는 건 if 문 세 개다.
게다가 git 호출에 `-- <docs>/solutions/` pathspec 을 함께 주면 경로 필터가 **git 과 파이썬 두 곳**에
생겨 드리프트한다.

대신 기존 `_compounded(...) -> bool` 을 `_solution_notes(...) -> list[str]` 로 바꿨다. 반환 타입만
넓혔는데 도착 판정이 그 목록 위에서 돌게 되어 필터가 한 곳으로 모였고, 기존 selftest 케이스 6개가
그대로 살아남았다.

- **분기만 있는 함수를 뽑으면 커버리지는 오르고 보증은 그대로다.** 추출할 값이 있는지 보려면
  "이 함수에서 틀릴 수 있는 게 무엇인가"를 묻는다. 답이 "없음"이면 인라인이 맞다.
- 이미 있는 함수의 **반환 타입을 넓히는 것**이 새 함수를 만드는 것보다 먼저다 — 호출부가 하나 늘 뿐
  테스트 자산이 유지된다.

→ [GUARDRAILS.md](GUARDRAILS.md) 에 승격.

## 부수 교훈 2 — 임시 레포 probe 는 만든 상태를 되짚어 확인한다

계획 전에 git 동작을 실측하려고 임시 레포 스크립트를 짰다([probe-constraints-before-planning.md]
(probe-constraints-before-planning.md) 규칙). **첫 시도가 조용히 어긋났다.**

```bash
set -e
git push -q -u origin main && git remote set-head origin -a   # bare repo 라 HEAD 미설정 → 실패
git checkout -qb PHASE && echo code > code.txt
git commit -qam feat                                          # -a 는 untracked 를 안 담는다 → 빈 커밋 시도
```

`set -e` 는 멈추지 않았고, `git commit -am` 은 새 파일 `code.txt` 를 담지 않아 **의도한 브랜치 구조가
아예 만들어지지 않았다.** 그런데도 스크립트는 끝까지 돌아 그럴싸한 출력을 냈다 — 결과 표만 보면
성공한 probe 처럼 보인다.

두 번째 시도에서 `git add -A` 로 바꾸고 bare repo 의 `HEAD` 를 명시적으로 세운 뒤,
`base(origin/HEAD) = origin/main` 을 **출력에 찍어** 전제가 성립하는지 확인했다.

- **probe 스크립트는 결과만 보지 말고 "만들려던 상태가 만들어졌는지"를 함께 출력한다.**
  브랜치 구조·base ref 처럼 전제가 되는 값은 판정 전에 찍는다.
- `git commit -am` 은 **추적 중인 파일만** 담는다. 새 파일을 만드는 fixture 에서는 `git add -A` 를 쓴다.
- `set -e` 는 `&&` 체인 끝의 실패를 항상 잡아 주지 않는다. probe 는 실패를 조용히 넘기는 쪽이 기본값이라고
  보고, 중간 상태를 확인하는 출력을 끼워 넣는다.

→ [GUARDRAILS.md](GUARDRAILS.md) 에 승격.

## 부수 교훈 3 — 못 막는 것은 게이트를 넓히지 말고 거짓말을 멈춘다

gh 로 판정할 수 **없는** 레포(비-GitHub·오프라인·PR 없음)에서는 여전히 solutions 밖 작업을 게이트로
지킬 수 없다. 그 경로는 **출력**으로 받았다.

```python
# before — -d 가 실패해도 무조건
print(f"  ✓ '{slug}' 정리 완료.")

# after — 남았으면 남았다고 말하고 확인 방법을 준다
else:
    print(f"  ⚠ 브랜치 {branch} 를 남겨뒀어요 — git 이 미머지로 봐요.")
    print("    squash 머지면 정상이지만, 내용을 확인하기 전엔 -D 로 지우지 마세요:")
    print(f"      git diff origin/{base} {branch}")
```

이슈가 꼽은 실제 피해 경로는 "커밋이 지워졌다"가 아니라 **"`✓` 를 보고 사람이 다음 수순으로 `-D` 를 눌렀다"**
였다. 게이트를 넓히면 오탐으로 막히지만, 출력은 오탐 비용이 0이고 solutions 밖 파일까지 전부 커버한다.

- **판정할 수 없는 것을 게이트로 만들려 하지 말고, 판정할 수 없다는 사실을 사용자에게 정확히 말한다.**
  `✓` 는 보증이다. 보증할 수 없으면 찍지 않는 것이 가장 싼 수정이다.

→ [GUARDRAILS.md](GUARDRAILS.md) 에 승격.

## 특이사항 — 번호 붙은 문서는 끝에 붙인다

`docs/ADR.md` 에 ADR-012 를 추가할 때 Edit 로 ADR-011 **앞에** 삽입해 번호 순서를 깼다
(011 이 012 뒤에 오는 상태). 파일 끝을 찾는 것보다 기존 헤딩을 앵커로 쓰는 게 쉬워 보였던 것뿐이고,
얻는 건 없었다. 오름차순 문서에 항목을 더할 때는 append 가 기본이다. 잡은 방법은 헤딩 목록을 찍어 본 것:

```bash
grep -n "^### ADR-" docs/ADR.md
```

GUARDRAILS 로 올릴 만큼 일반적이진 않아 여기에만 남긴다.

관련: [verification-trigger-coverage.md](verification-trigger-coverage.md) (역방향으로 트리거를 먼저 확인),
[pr-scope-two-dot-diff.md](pr-scope-two-dot-diff.md) (2-dot 과 3-dot 은 다른 질문이다),
[probe-constraints-before-planning.md](probe-constraints-before-planning.md) (계획 전 임시 리소스 실측),
[ci-check-coverage.md](ci-check-coverage.md) (게이트가 실제로 막는지 양방향 실증)
