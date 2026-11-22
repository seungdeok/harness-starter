#!/usr/bin/env python3
"""산문(SKILL.md·CLAUDE.md 미러)에 대한 결정론적 검사 — GUARDRAILS 에서 옮겨 온 규칙.

  1. 스킬 산문의 셸 명령에 `ls *.ext` 금지 — zsh nomatch 에러는 2>/dev/null 로 안 막힌다 (find 를 쓴다)
  2. `cmd -- $files` 금지 — zsh 는 단어 분할을 안 해 목록이 인자 하나로 뭉친다
  3. 루트 CLAUDE.md ↔ templates/CLAUDE-guidelines.md 본문, CLAUDE-docs.md 의 @import 줄 미러 동기화
근거: docs/solutions/skill-prose-commands.md · verification-trigger-coverage.md · plugin-target-repo-no-dependency.md
Self-check: python3 scripts/check-prose.py --test
"""
import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINE_RULES = [
    (re.compile(r"(?:^|[\s`;&|(])ls\s[^\n`|]*\*"),
     "`ls *.ext` 금지: zsh 의 glob nomatch 에러는 2>/dev/null 로 안 막혀요. `find <dir> -name '*.ext'` 를 쓰세요."),
    (re.compile(r"\s--\s+\$(?:\w|\{)"),
     "`cmd -- $files` 금지: zsh 는 단어 분할을 안 해 목록이 인자 하나로 뭉쳐요. `\"${(f)files}\"` 를 쓰세요."),
]


def line_errors(path: Path, text: str):
    for n, line in enumerate(text.splitlines(), 1):
        for pat, reason in LINE_RULES:
            if pat.search(line):
                yield f"{path.relative_to(ROOT)}:{n}: {reason}"


def mirror_view(root_md: str) -> str:
    """허용 차이(제목·§7·Project Docs)를 걷어 낸다 — 루트 전용 절을 추가하면 여기도 고친다."""
    body = root_md.split("\n---\n\n## Project Docs", 1)[0]
    body = re.sub(r"\n## 7\..*?(?=\n---\n)", "", body, flags=re.S)
    return body.split("\n", 1)[1].strip()


def template_view(tpl: str) -> str:
    return tpl.replace("{{DOCS_PATH}}", "docs").split("\n", 1)[1].strip()


def imports(md: str) -> list:
    return [l for l in md.replace("{{DOCS_PATH}}", "docs").splitlines() if l.startswith("@")]


def mirror_errors(name: str, root: list, tpl: list):
    if root != tpl:
        diff = "\n".join(difflib.unified_diff(root, tpl, "CLAUDE.md", name, lineterm="", n=1))
        yield f"CLAUDE.md ↔ {name} 미러가 갈렸어요 — 대상 레포에만 규범이 빠지지 않게 같이 고치세요.\n{diff}"


def main() -> int:
    errors = []
    for p in sorted((ROOT / "skills").rglob("*.md")):
        errors += line_errors(p, p.read_text())
    root_md = (ROOT / "CLAUDE.md").read_text()
    tpl = ROOT / "skills/setup/templates"
    errors += mirror_errors("CLAUDE-guidelines.md", mirror_view(root_md).splitlines(),
                            template_view((tpl / "CLAUDE-guidelines.md").read_text()).splitlines())
    errors += mirror_errors("CLAUDE-docs.md", imports(root_md), imports((tpl / "CLAUDE-docs.md").read_text()))
    for e in errors:
        print(e, file=sys.stderr)
    return 1 if errors else 0


def _test():
    bad = ["ls .github/*.md", "`ls docs/*.md 2>/dev/null`", "git diff --quiet -- $files", "cmd -- ${files}"]
    good = ["find .github -name '*.md'", "ls -la", "git diff -- \"${(f)files}\"", "echo glob *", "--name-status"]
    for s in bad:
        assert any(p.search(s) for p, _ in LINE_RULES), s
    for s in good:
        assert not any(p.search(s) for p, _ in LINE_RULES), s
    root = "# T\n\nA {x}\n\n## 7. c\n\nseven\n\n---\n\nfoot\n\n---\n\n## Project Docs\n\nd"
    assert mirror_view(root) == template_view("# U\n\nA {x}\n\n---\n\nfoot\n")
    assert mirror_view(root) != template_view("# U\n\nB\n\n---\n\nfoot\n")
    assert mirror_view(root.replace("A {x}", "A docs")) == template_view("# U\n\nA {{DOCS_PATH}}\n\n---\n\nfoot")
    assert imports("x\n@{{DOCS_PATH}}/A.md\n`@`") == imports("y\n@docs/A.md") == ["@docs/A.md"]
    assert list(mirror_errors("t", ["a"], ["b"])) and not list(mirror_errors("t", ["a"], ["a"]))
    print("ok")


if __name__ == "__main__":
    _test() if "--test" in sys.argv else sys.exit(main())
