# Architecture Decision Records

## 철학
<이 프로젝트의 의사결정 원칙 한 단락>

---

### ADR-001: 파이프라인 phase 규칙 — 브랜치 이름과 compound 분리
**결정**: `/pipeline` 파이프라인에서 phase 브랜치는 입력한 이름(slug)을 대문자로 한 `<SLUG>`(예: `SHARE-FORTUNE`, `feat-` 접두어 없음)로 만든다. compound(교훈 기록, CLAUDE.md 5장)는 파이프라인 stage 에서 빼고 `/ce-compound` 로 수동 실행한다.
**이유**: 브랜치는 phase 이름과 1:1로 눈에 띄게 대응시키는 편이 추적이 쉽다. compound 는 사람이 회고를 판단해야 하는 단계라 자동화 stage 로 묶으면 형식적 기록만 남는다.
**트레이드오프**: compound 를 파이프라인 밖에 두면 빼먹을 수 있다 → make-pr 종료 시 `/ce-compound` 안내로 완화. 대문자 브랜치는 대소문자 구분 없는 파일시스템/툴에서 충돌 여지가 있으나 현재 워크플로우에선 문제 없음.

---

### ADR-002: 레포 자체를 Claude Code plugin(`harness`)으로 패키징
**결정**: 이 레포 루트에 `.claude-plugin/{plugin.json, marketplace.json}` 을 두어 레포 = plugin = marketplace 로 만든다. 스킬(pipeline·make-pr·make-issue)은 `skills/` 로 이동하고 `pipeline.py` 는 `skills/pipeline/scripts/` 에 번들한다. install-time 스크립팅이 없으므로 프로젝트 초기화는 `/harness:setup` 스킬이 담당한다: scope(글로벌=번들 스크립트+phases 만 / 프로젝트=pipeline.py·docs·CLAUDE.md 전부 복사)와 docs 경로를 물어 `.claude/harness.json` 에 저장하고, CLAUDE.md 는 마커(`<!-- harness:start/end -->`) append 만 한다. `plugin.json` 의 `version` 은 생략해 커밋 SHA 가 버전이 되게 한다. gstack 벤더 스킬(plan-ceo-review/plan-eng-review)은 plugin 에서 제외하고 `.claude/skills/` 에 남긴다.
**이유**: 레포 하나로 개발·배포·업데이트(`/plugin marketplace update`)가 끝난다. version 생략은 push=업데이트라 "쉬운 업데이트" 요구에 부합. CLAUDE.md append-only 는 사내 프로젝트의 기존 지침 보호. `pipeline.py` 의 ROOT 를 스크립트 위치 → cwd 기준 git root 로 바꿔 글로벌 캐시에서 실행해도 대상 레포에 phase 가 생기고 worktree 동작이 유지된다.
**트레이드오프**: 프로젝트 scope 로 복사된 `pipeline.py` 는 plugin 업데이트를 자동으로 받지 못한다 → setup 재실행으로 갱신 안내. plugin 활성화는 보안상 커밋 설정으로 공유 불가 → README 의 settings.local.json 안내로 완화(claude-plugin-config-scope.md 학습).
