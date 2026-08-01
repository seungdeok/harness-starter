# Changelog

사용자가 체감하는 변경만 최신순으로 적어요. `/plugin marketplace update` 를 돌린 뒤 무엇이 바뀌었는지 여기서 확인해요.

`plugin.json` 에 `version` 이 없어 **커밋 SHA 가 곧 버전**이에요(ADR-002). 그래서 버전 번호 대신 날짜로 묶고, 항목마다 이슈/PR 번호를 달아요.

## 2026-08-02

- `pipeline.py done` 의 compound 게이트가 이제 교훈이 `origin/<base>` 에 **도착했는지**까지 확인해요. 전에는 로컬 커밋만 있어도 통과해서 `✓ 정리 완료` 가 거짓 안심을 줬어요 — push·머지가 안 됐으면 거부하고, 메시지로 무엇을 해야 하는지 알려줘요. `--force` 우회는 그대로예요. ([#32](https://github.com/seungdeok/harness-starter/issues/32))

## 2026-08-01

- 이 문서(`CHANGELOG.md`)를 신설. 이제 업데이트 후 무엇이 바뀌었는지 확인할 수 있어요. ([#24](https://github.com/seungdeok/harness-starter/issues/24))
- 플러그인 매니페스트에 라이선스(MIT)를 명시. ([#24](https://github.com/seungdeok/harness-starter/issues/24))
- 매니페스트 검증(`claude plugin validate`)을 `.claude-plugin/` 이 바뀔 때만 돌도록 분리했어요 — 매니페스트와 무관한 PR 이 Claude Code CLI 릴리스에 영향받지 않아요. ([#24](https://github.com/seungdeok/harness-starter/issues/24))

---

이 문서 이전의 변경은 [커밋 히스토리](https://github.com/seungdeok/harness-starter/commits/main)에서 볼 수 있어요.
