# Architecture Decision Records

## 철학
<이 프로젝트의 의사결정 원칙 한 단락>

---

### ADR-001: 파이프라인 phase 규칙 — 브랜치 이름과 compound 분리
**결정**: `/pipeline` 파이프라인에서 phase 브랜치는 입력한 이름(slug)을 대문자로 한 `<SLUG>`(예: `SHARE-FORTUNE`, `feat-` 접두어 없음)로 만든다. compound(교훈 기록, CLAUDE.md 5장)는 파이프라인 stage 에서 빼고 `/ce-compound` 로 수동 실행한다.
**이유**: 브랜치는 phase 이름과 1:1로 눈에 띄게 대응시키는 편이 추적이 쉽다. compound 는 사람이 회고를 판단해야 하는 단계라 자동화 stage 로 묶으면 형식적 기록만 남는다.
**트레이드오프**: compound 를 파이프라인 밖에 두면 빼먹을 수 있다 → make-pr 종료 시 `/ce-compound` 안내로 완화. 대문자 브랜치는 대소문자 구분 없는 파일시스템/툴에서 충돌 여지가 있으나 현재 워크플로우에선 문제 없음.
