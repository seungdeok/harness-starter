# 테스트

이 레포는 **빌드 단계가 없어요** — 스킬은 마크다운, `pipeline.py` 는 stdlib 파이썬이에요.
그래서 "테스트"의 절반은 자동 검사가 아니라 **임시 레포 probe** 예요.

## 어떤 명령으로 돌리나

```bash
# 순수 로직 (cursor·advance·slug) — CI: validate.yml, 모든 PR 에서 실행
python3 skills/pipeline/scripts/pipeline.py selftest

# 플러그인 매니페스트 — CI: plugin-validate.yml, .claude-plugin/** 이 바뀔 때만 (ADR-010)
claude plugin validate .

# 이 레포 안에서 스킬을 직접 써보기 (dogfooding)
claude --plugin-dir .
```

전제: `python3` 만 있으면 돼요. `claude plugin validate` 는 Claude Code CLI 가 필요하고
버전을 고정하지 않았어요 (ADR-010 — dependabot 이 없어 고정하면 검증이 영영 낡아요).

## 무엇을 테스트하고, 무엇을 안 하나

| 대상 | 테스트하나 | 왜 |
| --- | --- | --- |
| `pipeline.py` 순수 함수 (cursor·advance·slug·`_blocking`·`_solution_notes`) | ✅ `selftest` | 로직이 있고 git 없이 돌아가요 |
| `done` 의 compound 게이트 3분기·도착 판정 | ❌ | git·`gh` 호출에 의존해 `selftest` 로 못 덮어요 → 임시 레포 실증으로 대신해요 (ADR-012) |
| `.claude-plugin/*.json` | ✅ `claude plugin validate` | 깨지면 플러그인 전체가 설치 불가라 파급이 커요 |
| `skills/**/SKILL.md` (산문 절차) | ❌ **어떤 CI 도 안 봐요** | `validate` 는 매니페스트만 봐요 — 실측했어요 (`ci-check-coverage.md`, issue #15) |
| `docs/**` 링크·앵커 | ❌ | 변경 시 스크립트로 1회 확인하고 끝내요 (상시 검사 없음) |

**가장 큰 구멍은 산문이에요.** `SKILL.md` 는 이 레포에서 가장 자주 바뀌는 파일 축에 드는데
자동 검사가 0이에요. 아래 probe 절차가 그 자리를 메워요.

## 새 코드에 테스트를 어디까지 붙이나

- `pipeline.py` 에 **로직이 있는 순수 함수**를 추가하면 `selftest` 에 케이스를 같이 넣어요.
- **분기만 있는 코드는 함수로 뽑지 않아요.** "이 함수에서 틀릴 수 있는 게 무엇인가"에 답이 없으면
  인라인이 맞아요 — 뽑으면 커버리지만 오르고 보증은 그대로예요 (`gate-ref-symmetry.md`).
- CI 체크를 추가하면 **일부러 깨뜨려 `exit 1` 이 나오는지** 확인해요. 통과만 본 체크는
  실제로 막는지 알 수 없어요 (GUARDRAILS).

## 검증을 어떻게 남기나

산문·절차 변경은 테스트가 없으니 **임시 레포 probe** 로 실증하고, 그 결과를 PR 본문과
해결 노트에 남겨요. ADR-008·ADR-012·ADR-013 이 전부 이 방식이에요.

```bash
# 1. $TMPDIR 아래에 임시 git 레포를 만들고 fixture 를 심는다
#    (git commit -am 은 untracked 를 안 담으니 git add -A 를 쓴다)
# 2. 절차를 그대로 적용한다 — 부품이 아니라 절차 전체를,
#    최초 실행과 재실행 두 상태로 (GUARDRAILS 2026-08-02)
# 3. 결과만 보지 말고 "만들려던 상태가 만들어졌는지"를 함께 출력한다
# 4. 역방향 확인: 조건을 뒤집어 결과가 실제로 뒤집히는지 본다.
#    안 뒤집히면 통과한 게 아니라 아무것도 안 돈 것이다
# 5. 만든 것만 지운다 — 부모 디렉토리 rm -rf 는 추적 파일까지 가져간다
```

probe 를 지운 뒤 `git status` 로 예상 밖 삭제가 없는지 확인해요.

## 이 프로젝트에서 자주 깨지는 것

실제로 겪은 것만 적어요. 자세한 맥락은 `solutions/` 의 해결 노트에 있어요.

- **정방향만 확인하고 통과로 읽기** — 대상 코드 경로를 안 밟았는데 초록불이 떠요.
  (`verification-trigger-coverage.md`)
- **squash 머지를 도달 가능성으로 판정** — `branch -d`·`git log A..B`·`git cherry` 가 전부
  "미머지"라고 답해요. (`gate-ref-symmetry.md`)
- **zsh 에서 매칭 0건** — `ls *.ext` 의 nomatch 에러는 `2>/dev/null` 로 안 막혀요. `find` 를 써요.
  셸 변수에 담은 파일 목록을 `cmd -- $files` 로 넘기는 것도 조용히 "차이 없음"이 돼요.
  (`skill-prose-commands.md`, `verification-trigger-coverage.md`)
- **`gh` 의 플래그·`--json` 필드가 설치된 버전에 없음** — 공식 문서에 있어도 구버전엔 없어요.
  (`gate-ref-symmetry.md`)
- **재실행에서만 도달하는 조건이 죽어 있음** — 부품 검증은 전부 초록불이었어요.
  (`procedure-level-changes.md`)
