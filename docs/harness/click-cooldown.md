# 클릭 어뷰징 방지 — 광고별 클릭 쿨다운 (#25)

## 문제

`recordClick`이 무제한으로 클릭을 집계해 연타/자동 클릭이 그대로 CPC 적립에 샜다. PRD 핵심 지표("실제 수익 $1")의 신뢰도가 무너지는 리스크.

## 원인

클릭 집계에 레이트 제한이 없었다. 리워드 광고의 표준 방어(액션 레이트 제한)가 부재.

## 해결

- `src/shared/abuseGuard.js`(신규, 순수): `isClickWithinCooldown(lastAt, now, cooldownMs)` + `CLICK_COOLDOWN_MS=60s`. `now` 주입으로 `Date.now()` 없이 경계 테스트.
- `src/shared/store.ts`: `Tally.lastClickAt` 추가, `recordClick`이 쿨다운 내면 `save` 전 early-return, 유효 클릭에만 스탬프(무시된 클릭은 창을 갱신하지 않음).
- `test/abuseGuard.test.mjs`: 첫 클릭(`lastAt==null`)/직전/경계/직후 4 경계.
- 문서: PRD FR9 · ADR-008 · ARCHITECTURE. draft PR #28.

## 재발 방지 (이번 사이클 실행 중 헛디딤)

1. **`node --test`는 인자 없이** — package.json 그대로 실행한다. `node --test test/`처럼 디렉터리를 주면 그 안 **모든** 파일을 로드해 vitest 전용 `popup.test.tsx`까지 끌어와 `MODULE_NOT_FOUND`로 죽는다. 인자 없는 `node --test`는 이름 규칙(`*.test.{js,cjs,mjs}`)으로 발견해 `.tsx`를 건너뛴다.
2. **worktree에서 pipeline.py는 그 worktree의 자기 사본으로 호출** — `python3 scripts/pipeline.py`(worktree 내부). `../../../scripts/pipeline.py`(메인 사본)를 부르면 `ROOT=Path(__file__).parent.parent`가 메인 체크아웃으로 잡혀 worktree의 `phases/<slug>/phase.json`을 못 찾는다.
