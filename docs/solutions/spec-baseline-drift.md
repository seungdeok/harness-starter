---
date: 2026-08-01
track: knowledge
category: best-practices
title: 설계 문서의 "현재 상태"와 "이미 강제됨" 주장은 코드로 대조한 뒤에 계획한다
tags: [spec, baseline, deep-interview, gitignore, omc, namespace, scope]
---

# 설계 문서의 "현재 상태"와 "이미 강제됨" 주장은 코드로 대조한 뒤에 계획한다

- 날짜: 2026-08-01
- 작업/PR: 브랜치 `PIPELINE-FAIL-CLOSED-COMPOUND-GATE` (커밋 `0d6fc35`, `786ace2`)

## 문제

"AI Native OS 구축 계획"이라는 설계 문서를 받았다. §2 에 현재 상태 표가 있고, §7 에 v0 작업 9개가
완료 기준과 함께 정리돼 있었다. 문서 자체가 "§6(미검증)을 먼저 읽고 §7 을 실행 단위로 삼는다"고
지시했다.

문서를 믿고 §7 부터 착수했으면 **9개 중 7개가 헛일이었다.** 그리고 유일하게 진짜였던 구멍은
문서가 "이미 완화됨"으로 분류해 둔 항목이었다.

## 원인

### 1. baseline 이 레포보다 낡아 있었다

| 문서 §2 주장 | 실제 |
| --- | --- |
| `scripts/pipeline.py`, 스킬은 `.claude/skills/` | `skills/pipeline/scripts/pipeline.py` + `.claude-plugin/` — plugin 전환 완료 (ADR-002) |
| §7-6 "plugin 패키징" | 이미 끝남 |
| §7-3 "`.gitignore` 에 `.omc/`" | 이미 있음 |
| stage 6단계 | 실제 9~10단계 (ADR-004) |
| §7-5 phase 산출물 이동 | ADR-005 가 이미 그 경로를 검토하고 **거부**함 (issue #11) |
| §7-7 plan-first 훅 | ADR-007 이 "규범은 코드가 아니라 문서로" 선례를 세움 |

문서는 정직하게 틀린 게 아니라 **시점이 고정된 채로 정확했다.** 그 사이 ADR 이 여섯 개 쌓였다.

### 2. "이미 강제된다"는 주장이 유일한 진짜 구멍을 가렸다

§3.3 이 이렇게 적었다: *"현 stage 순서(`make-pr → compound`)가 이미 이것을 강제한다."*
그래서 §10 리스크 표는 "compound 누락"을 **완화됨**으로 분류했다.

실제로는 ADR-001 이 compound 를 파이프라인에서 빼냈고, `skills/pipeline/SKILL.md` 는 **항상**
`--no-compound` 로 `init` 한다. `cmd_done` 은 compound 여부를 보지 않고 worktree 를 지웠다.
즉 문서가 "완화됨"으로 적어 둔 칸이 실은 열린 구멍이었고, **완화됐다는 서술이 그걸 안 보이게 했다.**

미검증 항목(V-1)은 30초 만에 실증됐고 이미 코드에서 쓰이고 있었다(`_main_root()`).
검증이 필요했던 건 "미검증"이라고 표시된 칸이 아니라 **"확인됨"이라고 표시된 칸**이었다.

### 3. 남의 도구 디렉토리를 빈 자리로 가정했다

문서 §3.2·§4.1 은 축적물을 `.omc/wiki/` 에 두라고 했다. 그런데 `.omc/wiki/` 는 OMC 의 라이브
데이터스토어다 — `index.md` 자동 재생성, `log.md` append-only, `wiki_lint`·`wiki_ingest` MCP 툴,
세션 훅이 같은 디렉토리에 쓴다. 이름이 비어 보인다고 빈 게 아니었다.

## 해결

착수 전에 레포를 읽고 문서와 대조했다. 그 결과 v0 9개 → **실제로 안 된 것 2개**로 줄었고,
방향이 세 번 바뀌었다(무커밋 폐기 · 축적 위치 유지 · 훅 폐기).

남은 둘만 구현했다.

- `_git_root()` fail-closed — git 밖에서 `Path.cwd()` 로 폴백해 조용히 엉뚱한 곳에 `phases/` 를
  만들던 것을 `sys.exit` 로. `ROOT` 가 모듈 로드 시점 평가라 `selftest`·`--help` 도 repo 안에서만
  돈다(의도된 비용, docstring 에 명시).
- `cmd_done` compound 게이트 — 정리 전에 그 브랜치가 `<docs>/solutions/` 를 건드렸는지 확인하고,
  아니면 아무것도 지우지 않고 거부. base 는 `origin/HEAD` 에서 읽고(하드코딩 아님),
  범위는 `origin/<base>...<branch>` three-dot, docs 경로는 `HARNESS_DOCS_PATH` 반영,
  origin 이 없으면 차단이 아니라 경고. `--force` 로 우회.

축적 위치는 옮기지 않고 `docs/` 를 유지하되, OMC 의 wiki 를 커밋 대상으로 올렸다.
여기서 `.gitignore` 를 두 번 잘못 짚었다.

**(a) 디렉토리 패턴에 경로 구분자가 없으면 모든 깊이를 매칭한다.**
기존 `.omc/` 는 `skills/.omc/` 까지 덮고 있었다. 루트만 노리려고 `.omc/*` 로 바꾸자(슬래시가
들어가 루트 고정) 숨어 있던 `skills/.omc/`(잘못된 cwd 로 실행된 흔적)가 추적 대상으로 새어 나왔다.
`*/**/.omc/` 한 줄로 막았다.

**(b) 중첩 `.gitignore` 가 루트를 이긴다 — 그리고 도구가 그걸 되돌린다.**
루트에 `!.omc/wiki/` 를 넣었는데도 계속 무시됐다. `git check-ignore -v` 가 범인을 지목했다:
OMC 가 `.omc/.gitignore` 에 `wiki/` 를 써서 자기 wiki 를 스스로 무시하고 있었다.
소스를 보니 재생성 조건이 `content.includes('wiki/')` — **부분 문자열** 검사였다.
`!wiki/` 로 두면 그 검사를 통과해 덧붙이지 않는다. 이 파일도 함께 커밋해야 clone 직후
첫 OMC 실행에서 다시 무시되지 않는다.

## 재발 방지

- **설계 문서를 실행 단위로 삼기 전에 "현재 상태" 절을 레포로 대조한다.** 문서는 시점이 고정되고
  코드는 안 그렇다. 이번엔 9개 중 7개가 이미 끝났거나 이미 거부된 안이었다.
- **문서가 "이미 강제된다/완화됨"이라고 적은 칸을 우선 검증한다.** "미검증"이라 표시된 칸은
  사람이 이미 의심하고 있어서 오히려 안전하다. 위험한 건 아무도 다시 안 보는 "확인됨" 칸이다.
- **남의 도구 상태 디렉토리에 산출물을 두기 전에 그 도구가 그 경로를 쓰는지 소스로 확인한다.**
  이름이 비어 보이는 것과 비어 있는 것은 다르다.
- **`.gitignore` 를 고치면 `git check-ignore -v` 로 "무시돼야 할 것"과 "추적돼야 할 것"을 모두
  찍는다.** 패턴에 슬래시가 없으면 모든 깊이를 매칭하고, 중첩 `.gitignore` 는 루트를 이기며,
  도구가 자기 규칙을 매 실행 되돌릴 수 있다. 셋 다 조용히 실패한다.

관련: [probe-constraints-before-planning.md](probe-constraints-before-planning.md) (실측이 계획을
바꾼다 — 이번엔 V-1 실증이 컴포넌트 하나를 통째로 없앴다), [ci-check-coverage.md](ci-check-coverage.md)
(일부러 깨뜨려 확인한다 — 이번에도 compound 게이트를 차단·통과·`--force` 세 경로로 실증),
[pipeline.md](pipeline.md)
