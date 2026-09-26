"""Read-only, standard-library helpers for Claude Code and Codex workflows."""

import argparse
from datetime import date, datetime
from pathlib import Path
import re


SKILLS = {
    "today": "오늘질문", "interview": "모의면접", "reinforce": "보강",
    "wrap-up": "마무리", "topic": "주제정리", "coding": "코딩테스트",
    "format": "포맷", "memo": "메모", "weekly": "주간회고",
}
ROOT = Path(__file__).resolve().parent.parent


def count_text(path):
    """Count Unicode code points; normalize CRLF and ignore trailing newlines/BOM."""
    return len(Path(path).read_text(encoding="utf-8-sig").rstrip("\n"))


def changed_topics(root, day):
    """List markdown paths whose mtime falls on day in the machine's local zone."""
    root = Path(root)
    return sorted(
        path.relative_to(root).as_posix()
        for path in (root / "topics").rglob("*.md")
        if path.is_file() and datetime.fromtimestamp(path.stat().st_mtime).date() == day
    )


def check_skills(root, skills=None):
    """Check this vault's plain scalar metadata and common workflow references.

    This is a structural check of this project's wrappers, not a general YAML
    parser or a guarantee of either model's behavior.
    """
    root = Path(root).resolve()
    errors = []
    for key, korean in (SKILLS if skills is None else skills).items():
        workflow = root / "workflows" / (key + ".md")
        if not workflow.is_file():
            errors.append(f"Missing workflows/{key}.md")
        for folder, name in [(".agents", "prep-" + key), (".claude", korean)]:
            path = root / folder / "skills" / name / "SKILL.md"
            label = path.relative_to(root).as_posix()
            if not path.is_file():
                errors.append(f"Missing {label}")
                continue
            content = path.read_text(encoding="utf-8-sig")
            match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", content, re.S)
            if not match:
                errors.append(f"{label}: missing frontmatter")
                continue
            fields = {}
            for line in match.group(1).splitlines():
                field, separator, value = line.partition(":")
                if separator:
                    fields[field.strip()] = value.strip().strip('\"\'')
            if fields.get("name") != name:
                errors.append(f"{label}: name must be {name}")
            if not fields.get("description"):
                errors.append(f"{label}: description is required")
            body = content[match.end():]
            links = re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", body)
            targets = {(path.parent / link).resolve() for link in links}
            for expected in (root / "AGENTS.md", workflow):
                if expected not in targets or not expected.is_file():
                    errors.append(f"{label}: missing reference {expected.relative_to(root)}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    count = commands.add_parser("count-text", help="Count a UTF-8 answer-only file")
    count.add_argument("file", type=Path)
    changed = commands.add_parser("changed-topics", help="List topics changed on a local date")
    changed.add_argument("--date", type=date.fromisoformat, default=date.today())
    changed.add_argument("--root", type=Path, default=ROOT)
    check = commands.add_parser("check", help="Check both sets of skill wrappers")
    check.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        if args.command == "count-text":
            print(count_text(args.file))
        elif args.command == "changed-topics":
            for path in changed_topics(args.root, args.date):
                print(path)
        else:
            errors = check_skills(args.root)
            for error in errors:
                print(error)
            if errors:
                return 1
            print(f"OK: {len(SKILLS)} workflows, {len(SKILLS) * 2} skill wrappers")
    except (OSError, UnicodeError) as error:
        parser.exit(1, f"Error: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
