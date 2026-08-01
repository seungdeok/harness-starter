---
title: "omc gitignore layers — 루트와 중첩 규칙의 상호작용"
tags: ["gitignore", "omc", "wiki", "terminology"]
created: 2026-08-01T14:18:22.665Z
updated: 2026-08-01T14:18:22.665Z
sources: []
links: ["docs-vs-omc-wiki.md", "harness-plugin-scope-marketplace-sha.md"]
category: architecture
confidence: medium
schemaVersion: 1
---

# omc gitignore layers — 루트와 중첩 규칙의 상호작용

`.omc/wiki/` 를 커밋하기 위해 **두 개의 `.gitignore` 가 협력**한다. 한쪽만 보면 동작을 오해한다.

## 레이어

### 루트 `.gitignore`
```gitignore
.omc/*
!.omc/wiki/
!.omc/.gitignore
*/**/.omc/
```

- `.omc/` 가 아니라 **`.omc/*`** 인 이유: 디렉토리를 통째로 제외하면 하위를 `!` 로 되살릴 수 없다. (ADR-005 가 `phases/` 에서 겪은 것과 같은 제약)
- `.omc/*` 는 슬래시가 있어 **앵커드**라 `.omc` 의 **직계 자식만** 매칭한다 — `.omc/wiki` 자체는 잡지만 `.omc/wiki/foo.md` 는 안 잡는다.
- `!.omc/.gitignore` 로 중첩 파일도 커밋한다. 이게 없으면 **clone 직후 첫 OMC 실행에서 wiki 가 다시 무시된다.**
- `.omc/*` 는 루트 고정이라 하위 디렉토리의 `.omc` 가 샌다 → `*/**/.omc/` 를 함께 둔다(잘못된 cwd 로 실행된 흔적이므로 전부 무시).

### 중첩 `.omc/.gitignore`
```gitignore
!wiki/
wiki/session-log-*.md
wiki/log.md
wiki/environment.md
```

루트가 `.omc/wiki/` **안의 파일**을 매칭하지 않으므로, 그 자리를 중첩 파일이 채운다 (git: 깊은 `.gitignore` 가 상위를 이긴다).

**순서가 중요하다** — `!wiki/` 는 디렉토리 재포함이므로 파일 제외 줄은 반드시 그 **뒤**에 와야 한다. 앞에 두면 재포함이 나중에 와서 제외가 무효가 된다.

## OMC 가 자기 규칙을 되돌리는 문제

`oh-my-claudecode` 의 `src/hooks/wiki/storage.ts:59` (4.15.3 · 4.15.7 동일):

```ts
if (!content.includes('wiki/')) {
  atomicWriteFileSync(gitignorePath, content.trimEnd() + '\nwiki/\n');
}
```

- 판정은 **단순 부분 문자열 검사**다. 파일 어디든 `wiki/` 가 있으면 덧붙이지 않는다.
- 그래서 `!wiki/` 든 `wiki/log.md` 든 상관없이 조건이 false 가 되어 우리 규칙이 유지된다.
- **OMC 구현 세부에 의존하는 취약점**이다. 상류가 정확 매칭으로 바꾸면 `wiki/` 가 덧붙어 `index.md` 까지 무시된다 → 재검토 대상. (ADR-009 가 명시)

### 트리거는 쓰기(`withWikiLock`)다 — 읽기가 아니다
`ensureWikiDir` 를 부르는 건 `withWikiLock`(mutation boundary)과 `writePageUnsafe` / `updateIndexUnsafe` / `appendLogUnsafe` / `writeEnvironmentUnsafe` 다.

**`wiki_list` 는 부르지 않는다.** 이 규칙을 검증할 때 `wiki_list` 로 돌리면 아무 일도 안 일어나므로 "통과"로 오판한다. 실제 검증에는 `wiki_add` 같은 **쓰기**를 써야 한다. (실측: PR #30)

## 검증 방법

`.gitignore` 변경은 **조용히 실패**하므로 양방향으로 찍는다:

```bash
git check-ignore -v <무시되어야 할 경로>   # 출력 있음 + exit 0
git check-ignore -v <추적되어야 할 경로>   # 출력 없음 + exit 1
```

`git check-ignore` 는 **존재하지 않는 경로도 판정**하므로 probe 파일을 만들 필요가 없다.

OMC 재생성 내성은 역방향까지 본다: `wiki/` 문자열이 없는 내용으로 바꿔 쓰기를 트리거하면 실제로 `wiki/` 가 덧붙는지 확인 → append 경로가 살아 있음을 확인한 뒤에야 정방향 통과가 의미를 갖는다.

## 관련
[[docs-vs-omc-wiki]] · [[harness-plugin-scope-marketplace-sha]]

