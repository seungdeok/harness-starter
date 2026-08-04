---
date: 2026-08-01
track: knowledge
category: best-practices
title: 검증은 게이트보다 트리거를 먼저 의심한다 — 대상 코드가 안 돌면 정방향은 조건과 무관하게 통과한다
tags: [verification, gitignore, omc, wiki, negative-test, harness]
---

# 검증은 게이트보다 트리거를 먼저 의심한다 — 대상 코드가 안 돌면 정방향은 조건과 무관하게 통과한다

- 날짜: 2026-08-01
- 작업/PR: [#30](https://github.com/seungdeok/harness-starter/pull/30) (이슈 [#29](https://github.com/seungdeok/harness-starter/issues/29)), 브랜치 `OMC-WIKI-GITIGNORE`

## 문제

`.omc/.gitignore` 에 세 줄을 추가해 OMC 자동 생성물을 커밋 대상에서 뺐다. 수용 기준 중 하나가
**"OMC 세션을 한 번 더 돌려도 `.omc/.gitignore` 가 되돌아가지 않는다"** 였다.

검증은 이렇게 했다.

```
1. 새 8줄 상태로 wiki_list 실행
2. git diff -- .omc/.gitignore  →  내 변경만, wiki/ 덧붙지 않음
3. 통과 ✅
```

**이 통과는 아무것도 증명하지 않았다.**

## 원인

`wiki_list` 는 `.omc/.gitignore` 를 쓰는 코드 경로를 **아예 부르지 않는다.**

되돌리는 주체는 `oh-my-claudecode` 의 `src/hooks/wiki/storage.ts:48` `ensureWikiDir()` 이고,
그 함수의 호출자는 `withWikiLock`(mutation boundary)과 `writePageUnsafe` ·
`updateIndexUnsafe` · `appendLogUnsafe` · `writeEnvironmentUnsafe` — **전부 쓰기 경로**다.
`wiki_list` 는 "auto-maintained index 를 읽는다"고 명시된 **읽기** 툴이라 그 근처에도 안 간다.

즉 정방향 테스트는 이런 모양이었다.

| 실제로 확인한 것 | 확인했다고 믿은 것 |
| --- | --- |
| 아무 일도 안 일어나는 명령을 돌렸더니 파일이 안 변했다 | 우리 규칙이 append 조건을 통과시킨다 |

**트리거가 없으면 정방향은 조건이 참이든 거짓이든 똑같이 통과한다.** 파일이 안 변한 이유가
"조건이 false 라서"인지 "그 코드가 아예 안 돌아서"인지 구분할 정보가 결과에 들어 있지 않다.

### 기존 규칙이 이걸 못 잡는 이유

GUARDRAILS 에 이미 *"CI 체크를 추가하면 일부러 깨뜨려 `exit 1` 이 나오는지 확인한다"* 가 있다
(근거: [ci-check-coverage.md](ci-check-coverage.md)). 그건 **게이트가 실제로 막는가**를 보는 규칙이다.

이번 건은 게이트도 규칙도 멀쩡했다. 틀린 건 **검증을 돌리는 하네스**였다.
gitignore 규칙 자체를 깨뜨려 보는 테스트로는 절대 안 잡힌다 — 어느 쪽으로 깨뜨려도
`wiki_list` 는 여전히 아무것도 안 쓰기 때문이다.

## 해결

역방향을 **먼저** 돌려 트리거가 살아 있는지부터 확인했다.

```bash
# 1) 역방향 — append 가 실제로 일어나는 조건을 만든다
printf '# probe: no keyword here\n' > .omc/.gitignore
# → wiki_list 실행: 변화 없음 ❌  (트리거가 아니라는 증거)
# → wiki_add 실행: 파일에 `wiki/` 가 덧붙음 ✅  (append 경로 live 확인)

# 2) 그다음에야 정방향이 의미를 갖는다
cp <8줄 버전> .omc/.gitignore
# → wiki_add 실행: sha a0b395fa 불변 ✅
```

역방향이 **아무 일도 안 일어남**을 보여준 순간 `wiki_list` 가 트리거가 아니라는 게 드러났고,
호출 그래프를 grep 해서 진짜 트리거(`withWikiLock`)를 찾았다.

```bash
grep -rn "ensureWikiDir" src/   # 호출자를 눈으로 확인
```

## 재발 방지

- **정방향 통과를 근거로 삼기 전에, 그 실행이 대상 코드 경로를 실제로 밟는지 확인한다.**
  가장 싼 확인법은 역방향이다 — 조건을 뒤집었을 때 **결과가 달라져야** 트리거가 살아 있는 것이다.
  역방향에서도 아무 일이 없으면 통과한 게 아니라 **아무것도 안 돌았다.**
- 트리거를 고를 때 **읽기 툴과 쓰기 툴을 구분한다.** 부작용이 있는 코드는 대개 mutation
  boundary(락·트랜잭션·write 함수) 뒤에 있고, 읽기 경로는 그걸 우회하도록 설계돼 있다.
  이름만 보고 "그 도구를 돌리면 그 코드가 돌겠지"라고 가정하지 않는다 — 호출 그래프를 grep 한다.
- 이 규칙은 "게이트가 실제로 막는지 본다"([ci-check-coverage.md](ci-check-coverage.md))의
  **앞 단계**다. 게이트를 의심하기 전에 게이트가 호출되기는 하는지를 먼저 의심한다.

→ [GUARDRAILS.md](GUARDRAILS.md) 에 승격.

## 부수 확인 — 상류 의존은 버전을 명시해 둔다

이번 규칙은 `content.includes('wiki/')` 라는 **부분 문자열 검사**에 기대고 있다(ADR-009 가
이미 "상류가 바뀌면 재검토"로 표시해 둔 취약점). 캐시에 공존하는 두 버전(4.15.3 · 4.15.7)이
같은 로직인지 대조해 두면, 나중에 깨졌을 때 "언제부터"를 좁힐 수 있다.

```bash
grep -n -A3 "content.includes" .../oh-my-claudecode/4.15.3/src/hooks/wiki/storage.ts
grep -n -A3 "content.includes" .../oh-my-claudecode/4.15.7/src/hooks/wiki/storage.ts
```

관련: [ci-check-coverage.md](ci-check-coverage.md) (게이트가 막는지 양방향 실증),
[probe-constraints-before-planning.md](probe-constraints-before-planning.md) (외부 도구 제약은
계획 전에 실측), [spec-baseline-drift.md](spec-baseline-drift.md) (`.gitignore` 는
`git check-ignore -v` 로 양쪽을 모두 찍는다)

## 같은 실수의 두 번째 사례 — 빈 결과를 "통과"로 읽다 (같은 날, 정리 단계)

머지 후 브랜치를 지워도 되는지 확인하는 스크립트를 이렇게 썼다.

```bash
files=$(git diff --name-only main...$b)
d=$(git diff --name-only $b main -- $files)     # ← zsh 에서 무너진다
[ -z "$d" ] && echo "고유 내용 없음, 삭제 안전"
```

세 브랜치 모두 "✅ 삭제 안전"이 떴다. **거짓이었다** — 그중 하나에는 아직 push 안 된
compound 노트가 들어 있었다.

원인은 `wiki_list` 건과 판박이다. **zsh 는 따옴표 없는 파라미터 확장에 단어 분할을 하지 않는다**
(bash 와 다르다). `$files` 의 여러 줄이 pathspec **하나**로 뭉쳐 아무 파일도 매칭하지 못했고,
그래서 diff 가 비었다. 빈 결과의 뜻은 "차이가 없다"가 아니라 **"비교가 일어나지 않았다"** 였다.

올바른 확인은 pathspec 없이 상태 코드를 보는 것이다.

```bash
git diff --name-status "$b" main | awk '$1=="D"{print $2}'   # 브랜치에만 있는 파일
```

기존 GUARDRAILS 의 zsh 규칙은 **glob nomatch** 한정이라 이 케이스를 덮지 못했다.
zsh 에서 명령이 조용히 무력화되는 경로가 최소 둘이라는 뜻이다.

→ [GUARDRAILS.md](GUARDRAILS.md) 에 승격.
