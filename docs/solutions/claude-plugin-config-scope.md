---
date: 2026-07-05
track: knowledge
category: conventions
title: Claude Code 플러그인 설정은 공유 settings.json에 넣지 않기
tags: [claude-code, plugin, settings, compound-engineering]
---

# Claude Code 플러그인 설정은 공유 settings.json에 넣지 않기

## 문제

프로젝트의 `.claude/settings.json`(= git에 커밋되어 팀원과 공유되는 설정)에 compound-engineering 플러그인의 `enabledPlugins`와 `extraKnownMarketplaces`를 넣었더니, 해당 플러그인 설정이 **에러로 무시**됐다.

## 원인

Claude Code는 **보안상 공유 프로젝트 설정(`.claude/settings.json`)에서 플러그인 설치·마켓플레이스 등록을 허용하지 않는다.** 레포를 clone한 사람에게 임의의 GitHub 플러그인을 강제로 신뢰·설치시키는 걸 막기 위해서다.

이 키들이 유효한 위치는 다음 둘뿐이다:

- **사용자 전역**: `~/.claude/settings.json`
- **프로젝트 로컬**: `.claude/settings.local.json` (gitignore 대상, 커밋되지 않음)

## 해결

1. 공유 `.claude/settings.json`에서 `enabledPlugins` / `extraKnownMarketplaces` 두 키를 제거했다. (위험 명령어 차단용 Bash 훅 등 나머지 설정은 유지)
2. `.claude/settings.local.json`을 새로 만들어 그 두 키를 옮겼다.

   ```json
   {
     "enabledPlugins": {
       "compound-engineering@compound-engineering-plugin": true
     },
     "extraKnownMarketplaces": {
       "compound-engineering-plugin": {
         "source": { "source": "github", "repo": "EveryInc/compound-engineering-plugin" }
       }
     }
   }
   ```

3. `.gitignore`에 `.claude/settings.local.json`을 추가해 실수로 커밋되지 않게 했다.
4. 팀원이 각자 하네스를 켤 수 있도록 `README.md`에 설정 안내 섹션을 추가했다. (개인 로컬 설정은 사람마다 직접 만들어야 하므로, 커밋으로 공유가 안 되는 대신 문서로 공유)

## 재발 방지

- 플러그인/마켓플레이스 설정(`enabledPlugins`, `extraKnownMarketplaces`)은 **커밋되는 `.claude/settings.json`에 절대 넣지 않는다.** `.claude/settings.local.json`(개인 로컬) 또는 `~/.claude/settings.json`(전역)에만 둔다.
- 팀 전체가 동일한 플러그인/하네스를 쓰길 원하면, 설정을 커밋하는 대신 **README에 각자 로컬 설정을 만드는 방법을 문서화**한다.
