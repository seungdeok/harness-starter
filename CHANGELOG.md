# Changelog

사용자가 체감하는 변경만 최신순으로 적어요. `/plugin marketplace update` 를 돌린 뒤 무엇이 바뀌었는지 여기서 확인해요.

`plugin.json` 에 `version` 이 없어 **커밋 SHA 가 곧 버전**이에요(ADR-002). 그래서 버전 번호 대신 날짜로 묶고, 항목마다 이슈/PR 번호를 달아요.

## 2026-08-02

- `/harness:setup` 이 파일을 건드리기 전에 대상 전체를 훑어 `없음/동일/다름/판정불가` 를 보여주고, 확인을 **한 번만** 받아요. 끝나면 `생성/갱신/스킵` 을 파일 단위로 사유와 함께 요약해요 — 바뀐 게 없어도 출력해요. 구본이 넣은 `.gitignore` 의 `phases/` 줄도 확인 후 지울 수 있어요. ([#34](https://github.com/seungdeok/harness-starter/issues/34))

## 2026-08-01

- 이 문서(`CHANGELOG.md`)를 신설. 이제 업데이트 후 무엇이 바뀌었는지 확인할 수 있어요. ([#24](https://github.com/seungdeok/harness-starter/issues/24))
- 플러그인 매니페스트에 라이선스(MIT)를 명시. ([#24](https://github.com/seungdeok/harness-starter/issues/24))
- 매니페스트 검증(`claude plugin validate`)을 `.claude-plugin/` 이 바뀔 때만 돌도록 분리했어요 — 매니페스트와 무관한 PR 이 Claude Code CLI 릴리스에 영향받지 않아요. ([#24](https://github.com/seungdeok/harness-starter/issues/24))

---

이 문서 이전의 변경은 [커밋 히스토리](https://github.com/seungdeok/harness-starter/commits/main)에서 볼 수 있어요.
