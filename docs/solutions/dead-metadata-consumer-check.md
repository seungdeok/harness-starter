---
date: 2026-08-04
track: knowledge
category: best-practices
title: "\"소비자가 없다\"고 판단하기 전에 그 포맷을 만든 도구가 아직 읽는지 확인한다"
tags: [compound, frontmatter, tooling, ce-compound, docs, harness]
---

# "소비자가 없다"고 판단하기 전에 그 포맷을 만든 도구가 아직 읽는지 확인한다

- 날짜: 2026-08-04
- 작업/PR: [#37](https://github.com/seungdeok/harness-starter/pull/37), 브랜치 `DOCS-SSOT` (커밋 `3792ee5` → 정정 `26ba93c`)

## 문제

문서 포맷 정리 작업에서 `docs/solutions/` 노트 12장의 YAML frontmatter
(`date`·`track`·`category`·`title`·`tags`)를 **죽은 메타데이터로 보고 전부 지웠다.**
커밋하고 PR 까지 올린 뒤 사용자가 "이건 ce-compound 의 포맷이잖아"라고 지적해서 알았다.

지운 채로 머지됐다면 다음 `/ce-compound` 실행이 기존 노트를 못 찾아 **같은 주제의 노트를 중복으로**
만들고, 동시에 새 노트에는 frontmatter 를 다시 붙여서 "쓰지 않는다"고 적어 둔 규범과 도구의 실제
동작이 갈라졌을 것이다.

## 원인

판단 근거는 이랬다 — "ADR-011 로 `.omc/wiki` 를 버렸다. wiki 가 `tags` 로 검색하던 도구였다.
그러니 지금은 `tags` 를 읽는 도구가 없다."

전제는 맞았고 결론이 틀렸다. **없어진 소비자 하나만 확인하고, 살아 있는 소비자를 안 찾았다.**
실제 소비자는 그 frontmatter 를 **쓰는 도구 자신**이었다:

```
ce-compound/SKILL.md:224  "targeting frontmatter fields: tags:.*(<keyword1>|<keyword2>)"
ce-compound/SKILL.md:230  "Read only frontmatter (first 30 lines) of candidate files to score relevance"
ce-compound/SKILL.md:331  "Validate YAML frontmatter against references/schema.yaml"
```

`/ce-compound` 는 새 노트를 쓰기 전에 `tags:` 를 Grep 해 후보를 고르고, 후보의 frontmatter 30줄만
읽어 **"기존 노트를 갱신할지 새로 만들지"** 를 정한다. 즉 그 필드는 노트를 *읽는* 사람이 아니라
노트를 *쓰는 파이프라인* 이 소비한다 — 눈에 안 보이는 게 당연했고, 그래서 안 찾았다.

여기엔 더 일반적인 함정이 있다. **생산자가 살아 있으면 소비자가 없어도 그 포맷은 죽지 않는다.**
지워도 다음 실행에 다시 생기기 때문이다. "지웠는데 다시 생긴다"는 죽은 게 아니라는 신호다.

## 해결

- 노트 12장의 frontmatter 를 `origin/main` 에서 복원했다 (커밋 `26ba93c`).
- `docs/solutions/README.md` 에 **지우면 안 되는 이유**를 명시했다 — "ce-compound 가 `tags:` 를
  Grep 해 기존 노트 갱신 여부를 판단한다. 지우면 같은 주제 노트가 중복으로 쌓인다."
  `skills/setup/templates/solutions-README.md` 미러도 함께 고쳤다.
- ADR-011 의 `**후속**` 에 **지우려다 되돌린 사실과 이유**를 적었다. 결과만 남기면 다음 사람이
  같은 추론("wiki 를 버렸으니 tags 는 죽었다")을 다시 밟는다.

되돌리지 않은 것: `claude-plugin-config-scope.md` 에 보충한 `- 날짜:`/`- 작업/PR:` 줄.
그건 레포 노트 형식이 요구하는 것이라 frontmatter 와 무관한 별개 수정이었다.

## 재발 방지

**무언가를 "안 쓰인다"고 판단해 지우기 전에, 소비자와 생산자를 모두 찾는다.**
소비자 탐색은 세 곳을 본다 — 사람이 읽는 곳, 코드가 읽는 곳, 그리고 **그 포맷을 만든 도구 자신**.
마지막이 가장 잘 빠지는데, 생산 코드와 소비 코드가 같은 도구 안에 있어 레포 Grep 으로는 안 잡힌다.

값싼 판별법: **지웠을 때 다음 실행이 다시 만들어 놓는가.** 그렇다면 그건 죽은 산출물이 아니라
살아 있는 계약이고, 지우는 게 아니라 문서화할 대상이다.

→ [GUARDRAILS.md](GUARDRAILS.md) 에 승격.

## 부수 확인 — 되돌린 사실은 결과가 아니라 추론까지 적는다

정정 커밋에 "복원했다"만 적으면 다음 사람이 왜 지웠는지 몰라 같은 판단을 반복한다.
그래서 ADR-011 후속과 커밋 메시지 양쪽에 **틀린 전제("wiki 가 소비자다")를 명시**했다.
이 레포는 뒤집힌 결정을 지우지 않고 `**후속**` 을 붙이는 규칙이 이미 있는데
(ADR §철학), 그 규칙이 **자기 실수에도 적용된다**는 걸 이번에 확인했다.

## 관련

- [omc-wiki-page-authoring.md](omc-wiki-page-authoring.md) — 도구가 만든 파일의 파생 필드를
  손으로 고치면 어긋난다. 이번 건은 그 반대 방향(파생 필드를 **지우는** 쪽)의 같은 함정이다.
- [spec-baseline-drift.md](spec-baseline-drift.md) — "이미 강제된다/이제 안 쓰인다"는 문서의 주장을
  코드로 대조하기.
