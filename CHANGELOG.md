# Changelog

사용자가 체감하는 변경만 최신순으로 적어요. `/plugin marketplace update` 를 돌린 뒤 무엇이 바뀌었는지 여기서 확인해요.

`plugin.json` 에 `version` 이 없어 **커밋 SHA 가 곧 버전**이에요(ADR-002). 그래서 버전 번호 대신 날짜로 묶고, 항목마다 이슈/PR 번호를 달아요.

## 2026-08-05

- `/harness:setup` 이 `CLAUDE.md` 를 **두 조각으로 나눠** 넣어요 — 행동 가이드라인(A)과 `## Project Docs` @import 블록(B). `A 는 글로벌 · B 는 프로젝트` 를 고르면 여러 레포에서 가이드라인을 공유하면서 문서 참조만 레포별로 둘 수 있어요. 마커도 `harness:guidelines`/`harness:docs` 두 쌍으로 나뉘어요. **구본 `harness:start` 블록은 그대로 동작하고, 갱신을 고를 때만 교체돼요.** ([#38](https://github.com/seungdeok/harness-starter/issues/38))
- `<docs>/TESTING.md` 템플릿이 생겼어요 — 빈 헤딩이 아니라 "어떤 명령으로 돌리나 / 무엇을 안 테스트하나 / 검증을 어떻게 남기나" 질문에 답하는 형식이에요. `@import` 목록에도 들어가서 verify 할 때 자동으로 로드돼요. ([#38](https://github.com/seungdeok/harness-starter/issues/38))
- `@import` 가 가리키는 경로가 **실제로 있는지 확인**해요. docs 경로를 오타로 답하면 전에는 조용히 아무것도 안 가리켰는데, 이제 종료 안내에 경고가 떠요. ([#38](https://github.com/seungdeok/harness-starter/issues/38))
- 가이드라인을 글로벌에 넣으면 **되돌리는 방법**을 알려줘요. `~/.claude/CLAUDE.md` 는 레포 밖이라 `git revert` 가 안 통해요. ([#38](https://github.com/seungdeok/harness-starter/issues/38))

## 2026-08-04

- `/harness:setup` 의 사전 스캔에서 `.gitignore` 의 `phases/` 잔재 행을 뺐어요. 스캔이 유일하게 남의 파일을 지우자고 제안하는 행이었어요 — 잔재가 남아 있으면 직접 지워요 (ADR-005 이후 불필요한 줄이에요).
- 대상 레포에 복사되는 `<docs>/solutions/README.md` 에 **ADR·해결 노트·GUARDRAILS 가 각각 무엇을 담고 어떻게 서로 링크하는지** 표와 규칙이 생겼어요. `/ce-compound` 가 붙이는 frontmatter 를 지우면 안 되는 이유도 함께 적었어요.

## 2026-08-02

- `/harness:setup` 이 파일을 건드리기 전에 대상 전체를 훑어 `없음/동일/다름/판정불가` 를 보여주고, 확인을 **한 번만** 받아요. 끝나면 `생성/갱신/스킵` 을 파일 단위로 사유와 함께 요약해요 — 바뀐 게 없어도 출력해요. 구본이 넣은 `.gitignore` 의 `phases/` 줄도 확인 후 지울 수 있어요. ([#34](https://github.com/seungdeok/harness-starter/issues/34))
- `pipeline.py done` 이 브랜치를 못 지웠을 때 더 이상 `✓ 정리 완료` 로 덮지 않아요. `git branch -d` 는 squash 머지를 미머지로 보기 때문에 브랜치가 남는 건 흔한 정상 상황인데, `✓` 를 보고 `-D` 를 눌러 작업을 잃는 경로가 있었어요. 이제 남았다고 말하고 확인 명령을 알려줘요. ([#32](https://github.com/seungdeok/harness-starter/issues/32))
- `pipeline.py done` 이 `gh` 로 PR 상태를 봐서 머지 여부를 판정해요. PR 이 안 머지됐거나 **머지된 뒤에 붙은 커밋**이 있으면 거부해요 — squash 머지라 로컬 git 으로는 알 수 없던 것이고, `docs/solutions/` 밖 작업도 함께 지켜져요. `gh` 가 없거나 GitHub 레포가 아니면 기존 내용 비교로 자동 폴백해요. ([#32](https://github.com/seungdeok/harness-starter/issues/32))
- `pipeline.py done` 의 compound 게이트가 이제 교훈이 `origin/<base>` 에 **도착했는지**까지 확인해요. 전에는 로컬 커밋만 있어도 통과해서 `✓ 정리 완료` 가 거짓 안심을 줬어요 — push·머지가 안 됐으면 거부하고, 메시지로 무엇을 해야 하는지 알려줘요. `--force` 우회는 그대로예요. ([#32](https://github.com/seungdeok/harness-starter/issues/32))

## 2026-08-01

- 이 문서(`CHANGELOG.md`)를 신설. 이제 업데이트 후 무엇이 바뀌었는지 확인할 수 있어요. ([#24](https://github.com/seungdeok/harness-starter/issues/24))
- 플러그인 매니페스트에 라이선스(MIT)를 명시. ([#24](https://github.com/seungdeok/harness-starter/issues/24))
- 매니페스트 검증(`claude plugin validate`)을 `.claude-plugin/` 이 바뀔 때만 돌도록 분리했어요 — 매니페스트와 무관한 PR 이 Claude Code CLI 릴리스에 영향받지 않아요. ([#24](https://github.com/seungdeok/harness-starter/issues/24))

---

이 문서 이전의 변경은 [커밋 히스토리](https://github.com/seungdeok/harness-starter/commits/main)에서 볼 수 있어요.
