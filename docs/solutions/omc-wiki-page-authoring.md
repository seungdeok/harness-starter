---
date: 2026-08-01
track: knowledge
category: workflow-issues
title: OMC wiki 페이지를 손으로 고치면 파생 필드가 어긋난다 — links frontmatter 와 ASCII 슬러그
tags: [omc, wiki, frontmatter, slug, lint, tooling]
---

# OMC wiki 페이지를 손으로 고치면 파생 필드가 어긋난다 — links frontmatter 와 ASCII 슬러그

- 날짜: 2026-08-01
- 작업/PR: 브랜치 `WIKI-PROJECT-TERMS` (커밋 `55df246`, `4de540f`)

## 문제

`.omc/wiki/` 에 프로젝트 용어·함정 페이지 9장을 `wiki_add` 로 넣으면서 `[[page-name]]`
상호 링크를 걸었다. 두 가지가 조용히 어긋났다.

**1. `wiki_lint` 가 고친 링크를 계속 broken 이라고 했다.**

```
[ERROR] broken-ref: Broken link to "harness-plugin-terms.md" from "축적 레이어 ..."
```

본문의 `[[harness-plugin-terms]]` 를 올바른 슬러그로 다 고쳤는데도 리포트가 그대로였다.

**2. 제목이 슬러그로 안 옮겨졌다.**

`"git 범위 확인과 충돌 사전 검사"` 로 페이지를 만들었더니 파일이 **`git.md`** 가 됐다.

## 원인

### `links` 는 본문에서 실시간 파싱되지 않고 frontmatter 에 박힌다

`wiki_add` 는 쓰기 시점에 본문의 `[[...]]` 를 뽑아 frontmatter 에 고정한다.

```yaml
---
title: "pipeline 용어 — phase · slug · stage · worktree"
links: ["compound-loop-skills.md", "accumulation-layers.md", "harness-plugin-terms.md"]
---
```

`wiki_lint` 는 **본문이 아니라 이 `links` 필드**를 읽는다. 그래서 본문만 고치면 lint 는
영원히 옛 값을 본다. 반대로 `links` 만 고치고 본문을 안 고치면 lint 는 통과하는데
사람이 읽는 링크는 깨져 있다 — **두 표현이 갈라질 수 있는 구조**다.

### 슬러그는 제목의 ASCII 토큰만 쓴다

| 제목 | 결과 슬러그 |
| --- | --- |
| `pipeline 용어 — phase · slug · stage · worktree` | `pipeline-phase-slug-stage-worktree.md` |
| `축적 레이어 — 규범(docs) vs 사실(.omc/wiki)` | `docs-vs-omc-wiki.md` |
| `git 범위 확인과 충돌 사전 검사` | **`git.md`** ← ASCII 토큰이 `git` 하나뿐 |

한글은 슬러그에 안 들어간다. 그래서 **한글 위주 제목은 첫 영단어 하나로 뭉개지고**,
영단어가 흔한 것(`git`·`wiki`)이면 다음 페이지와 충돌하기 쉬운 이름이 된다.

`pipeline.py` 의 `_slug()` 는 한글을 보존하는데(`[^0-9a-zA-Z가-힣-]`) OMC wiki 는 아니다 —
**같은 레포에서 도는 두 도구의 슬러그 규칙이 서로 다르다.**

## 해결

**슬러그**: 제목 앞부분에 의미 있는 ASCII 토큰을 2개 이상 넣는다. 이미 뭉개진 페이지는
`wiki_delete` 후 재생성한다(파일명을 바꿀 방법이 그것뿐이다).

```
"git diff scope and merge conflict precheck — PR 범위·충돌 사전 검사"
→ git-diff-scope-and-merge-conflict-precheck-pr.md
```

**링크**: 본문을 진실의 원천으로 두고 `links` 를 **본문에서 재생성**한다. 손으로 두 곳을
맞추면 다음에 또 갈라진다.

```python
import re, pathlib
for p in sorted(pathlib.Path('.').glob('*.md')):
    if p.name == 'index.md':
        continue
    t = p.read_text(encoding='utf-8')
    m = re.match(r'(---\n.*?\n---\n)(.*)', t, re.S)
    if not m:
        continue                      # log.md 처럼 frontmatter 없는 파일
    fm, body = m.groups()
    seen, links = set(), []
    for s in re.findall(r'\[\[([^\]]+)\]\]', body):   # 본문에서만 뽑는다
        f = s if s.endswith('.md') else s + '.md'
        if f not in seen:
            seen.add(f); links.append(f)
    new = 'links: [' + ', '.join(f'"{l}"' for l in links) + ']'
    fm2, n = re.subn(r'^links: \[.*?\]$', new, fm, count=1, flags=re.M)
    if n:
        p.write_text(fm2 + body, encoding='utf-8')
```

**순서**: 페이지를 먼저 다 만들고 → 실제 파일명을 확인하고 → 그다음 링크를 건다.
슬러그를 예측해서 미리 링크를 걸면 이번처럼 broken-ref 를 5개 만들고 다시 고치게 된다.

`wiki_lint` 로 `0 broken refs` 를 확인하는 것으로 마무리한다.

## 재발 방지

- **도구가 생성한 파일을 손으로 고칠 때는 파생 필드도 함께 갱신한다.** 본문에서 파생된
  메타데이터(`links`·인덱스·요약)는 쓰기 시점 스냅샷이라, 본문만 고치면 검사 도구가
  옛 값을 계속 본다. 손으로 맞추지 말고 **본문에서 재생성**한다.
- **슬러그·ID 를 예측해서 참조를 미리 만들지 않는다.** 생성 → 실제 이름 확인 → 참조 연결
  순서로 간다. 도구마다 슬러그 규칙이 다르고(같은 레포 안에서도), 비-ASCII 처리는 특히 갈린다.

→ GUARDRAILS.md 에 승격.

## 부수 사항 — `index.md` 는 무시 대상 페이지도 링크한다

`index.md` 는 자동 재생성되고 **gitignore 를 모른다.** 그래서 커밋된 `index.md` 가
`session-log-*.md`(PR [#30](https://github.com/seungdeok/harness-starter/pull/30) 이 무시 대상으로
뺀 파일)를 계속 링크한다 → clone 직후 dead link 2개, 첫 OMC 쓰기에서 자동 복구.

손으로 지워도 다음 쓰기에 재생성되므로 **자동 생성 파일은 생성된 그대로 커밋**하고
별도 이슈로 다룬다. 원인이 OMC 상류(index 생성이 gitignore 를 안 봄)에 있다.

관련: [spec-baseline-drift.md](spec-baseline-drift.md) (남의 도구 상태 디렉토리는 소스로 확인한다 —
`.omc/wiki/` 가 라이브 데이터스토어라는 것도 거기서 나왔다)
