import os
from datetime import date, datetime
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

from scripts.vault_tools import changed_topics, check_skills, count_text


class VaultToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, path, text):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return target

    def test_count_normalizes_bom_and_windows_line_endings(self):
        target = self.root / "answer.txt"
        target.write_bytes("\ufeff가나다\r\nABC😀\r\n".encode("utf-8"))
        self.assertEqual(count_text(target), 8)

    def test_count_preserves_spaces_and_literal_shell_characters(self):
        text = '답변 $HOME `명령` $(문자열) "인용"  '
        target = self.write("answer.txt", text + "\n")
        self.assertEqual(count_text(target), len(text))

    def test_count_empty_file(self):
        self.assertEqual(count_text(self.write("empty.txt", "")), 0)

    def test_changed_topics_uses_requested_local_date_and_only_markdown(self):
        day = date(2026, 9, 26)
        for name, hour in [("concepts.md", 0), ("questions.md", 23)]:
            path = self.write("topics/java/" + name, "sample")
            stamp = datetime(2026, 9, 26, hour, 30).timestamp()
            os.utime(path, (stamp, stamp))
        for name in ["topics/java/old.md", "daily/2026-09-26.md", "topics/a.txt"]:
            path = self.write(name, "sample")
            stamp = datetime(2026, 9, 25 if name.endswith("old.md") else 26, 23, 59).timestamp()
            os.utime(path, (stamp, stamp))
        self.assertEqual(changed_topics(self.root, day), [
            "topics/java/concepts.md", "topics/java/questions.md"
        ])

    def test_changed_topics_missing_directory(self):
        self.assertEqual(changed_topics(self.root, date(2026, 9, 26)), [])

    def test_count_cli_accepts_path_with_spaces_and_threshold_answer(self):
        path = self.write("sample answers/answer.txt", "가" * 800 + "\n")
        script = Path(__file__).resolve().parents[1] / "scripts/vault_tools.py"
        result = subprocess.run([sys.executable, str(script), "count-text", str(path)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "800")

    def test_count_cli_missing_file_returns_failure(self):
        script = Path(__file__).resolve().parents[1] / "scripts/vault_tools.py"
        result = subprocess.run([sys.executable, str(script), "count-text",
                                 str(self.root / "missing.txt")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Error:", result.stderr)

    def make_skill_pair(self):
        self.write("AGENTS.md", "# Common rules\n")
        self.write("workflows/today.md", "# Workflow\n")
        for directory, name in [(".agents/skills/prep-today", "prep-today"),
                                (".claude/skills/오늘질문", "오늘질문")]:
            self.write(directory + "/SKILL.md", (
                f"---\nname: {name}\ndescription: 오늘 질문 선정\n---\n\n"
                "Read [rules](../../../AGENTS.md) and "
                "[workflow](../../../workflows/today.md).\n"
            ))

    def test_valid_pair_resolves_from_skill_directory(self):
        self.make_skill_pair()
        self.assertEqual(check_skills(self.root, {"today": "오늘질문"}), [])

    def test_check_reports_missing_workflow(self):
        self.make_skill_pair()
        (self.root / "workflows/today.md").unlink()
        self.assertTrue(any("workflows/today.md" in error
                            for error in check_skills(self.root, {"today": "오늘질문"})))

    def test_check_rejects_wrong_name_and_empty_description(self):
        self.make_skill_pair()
        self.write(".agents/skills/prep-today/SKILL.md",
                   "---\nname: wrong\ndescription: \n---\n")
        errors = check_skills(self.root, {"today": "오늘질문"})
        self.assertTrue(any("name" in error for error in errors))
        self.assertTrue(any("description" in error for error in errors))

    def test_check_rejects_wrapper_pointing_to_other_workflow(self):
        self.make_skill_pair()
        path = self.root / ".agents/skills/prep-today/SKILL.md"
        path.write_text(path.read_text(encoding="utf-8").replace(
            "workflows/today.md", "workflows/interview.md"), encoding="utf-8")
        self.assertTrue(check_skills(self.root, {"today": "오늘질문"}))


if __name__ == "__main__":
    unittest.main()
