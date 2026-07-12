# harness-starter

Compound Engineering **phase pipeline 하네스** 스타터. 새 프로젝트에 이 repo 내용을 복사하면
`plan → plan-review → implement → commit → make-pr → compound` 루프를 바로 돌릴 수 있어요.

## 들어있는 것

| 파일 | 역할 |
| ---- | ---- |
| `scripts/pipeline.py` | 의존성 0(stdlib) phase stage 체커 — `phases/<slug>/phase.json`으로 진행 추적 |
| `docs/solutions/pipeline.md` | 파이프라인 사용법 (대화형/headless 흐름) |
| `docs/solutions/README.md` | compound 루프 + CE 플러그인 활성화 안내 |
| `docs/solutions/GUARDRAILS.md` | 재발 방지 규칙 (처음엔 비어 있음, compound가 채움) |
| `docs/solutions/*.md` | 해결 노트 예시 2개 (형식 참고용) |
| `CLAUDE.md` | 행동 가이드라인 1~5장 + compound 루프 정의 |
| `.claude/skills/` | `plan-ceo-review`·`plan-eng-review`·`make-pr`·`make-issue` |
| `.claude/settings.json` | 위험 명령 차단 훅 |
| `docs/PRD.md`·`ADR.md`·`ARCHITECTURE.md` | 프로젝트 문서 템플릿 (CLAUDE.md가 참조) |

## 퀵스타트

```bash
python3 scripts/pipeline.py selftest          # 하네스 로직 확인 → "selftest OK"
python3 scripts/pipeline.py init "<작업명>"    # phase 시작 (전용 worktree + 브랜치 생성)
cd .claude/worktrees/<slug>                    # 이후 명령은 worktree 안에서
python3 scripts/pipeline.py status            # 지금 실행할 stage 확인
# 그 스킬을 세션에서 실행 후:
python3 scripts/pipeline.py advance --summary "<요약>"   # status→advance 반복
```

### 또는 자연어로 (프롬프트)

CLI를 직접 치지 않고 Claude에게 시켜도 돼요. `phase 파이프라인` 또는 `pipeline.py`가 들어가면
아래 흐름(`selftest → init → status → advance`)을 알아서 돌려요.

> **"<기능명> phase 파이프라인으로 작업 시작해줘"**

| 하고 싶은 것 | 이렇게 말하면 |
| --- | --- |
| 시작 | "결제 연동 기능 **phase 파이프라인으로 시작**해줘" |
| plan-review 생략 | "댓글 기능 phase로 시작하되 **plan review는 빼줘**" |
| 다음 stage | "**다음 stage 진행해**" / "advance 해줘" |
| 현재 위치 | "**지금 어느 stage야?**" |
| 전자동(headless) | "이 phase **끝까지 자동으로 돌려**" |

자세한 내용은 `docs/solutions/pipeline.md`.

## 필요한 스킬 (optional)

각 stage는 스킬을 실행해요. 로컬(`.claude/skills/`)에 없는 아래 두 개는 외부에서 켜야 해요 — 없으면 그 stage만 건너뛰면 돼요.

| stage | 스킬 | 출처 |
| --- | --- | --- |
| plan-review-ceo/eng | `/plan-ceo-review`·`/plan-eng-review` | **gstack** |
| compound | `/ce-compound` (+ `/ce-code-review`) | **compound-engineering@compound-engineering-plugin** |

compound-engineering 플러그인 활성화 방법은 `docs/solutions/README.md` 참고.

## 새 프로젝트에 적용

1. 이 repo 파일을 새 프로젝트 루트에 복사.
2. `docs/PRD.md`·`ADR.md`·`ARCHITECTURE.md`를 프로젝트 내용으로 채움.
3. compound 단계에서 배운 교훈을 `docs/solutions/`에 노트로 남기고, 규칙은 `GUARDRAILS.md`로 승격.
