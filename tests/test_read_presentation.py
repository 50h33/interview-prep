import hashlib
from unittest import mock
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/read_presentation.py"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def xml_escape(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))


class PresentationReaderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write_pptx(self, name="발표 자료.pptx", *, order=("r10", "r1"),
                   include_notes=True, image_only=False, missing_slide=False):
        path = self.root / name
        presentation = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            f'xmlns:r="{DOC_REL_NS}"><p:sldIdLst>'
            + "".join(f'<p:sldId id="{300 + index}" r:id="{rel}"/>'
                      for index, rel in enumerate(order))
            + '</p:sldIdLst></p:presentation>'
        )
        targets = {"r1": "slides/slide1.xml", "r10": "slides/slide10.xml"}
        rels = (
            f'<Relationships xmlns="{REL_NS}">'
            + "".join(
                f'<Relationship Id="{rel}" Type="{DOC_REL_NS}/slide" '
                f'Target="{target}"/>' for rel, target in targets.items()
            )
            + '</Relationships>'
        )
        slides = {
            "ppt/slides/slide1.xml": self.slide_xml("첫째 & <escaped>", image=image_only),
            "ppt/slides/slide10.xml": self.slide_xml("열째 한글", image=False),
        }
        if missing_slide:
            del slides["ppt/slides/slide1.xml"]
        with ZipFile(path, "w") as archive:
            archive.writestr("ppt/presentation.xml", presentation)
            archive.writestr("ppt/_rels/presentation.xml.rels", rels)
            for part, content in slides.items():
                archive.writestr(part, content)
            if include_notes and not missing_slide:
                archive.writestr(
                    "ppt/slides/_rels/slide1.xml.rels",
                    f'<Relationships xmlns="{REL_NS}"><Relationship Id="note" '
                    f'Type="{DOC_REL_NS}/notesSlide" Target="../notesSlides/notesSlide1.xml"/>'
                    '</Relationships>',
                )
                archive.writestr("ppt/notesSlides/notesSlide1.xml", self.notes_xml())
        return path

    @staticmethod
    def slide_xml(text, *, image=False):
        escaped = xml_escape(text)
        visual = '<p:pic><p:nvPicPr/><p:blipFill/></p:pic>' if image else ""
        return (
            '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            f'<p:cSld><p:spTree><p:sp><p:txBody><a:p><a:r><a:t>{escaped}</a:t>'
            f'</a:r></a:p></p:txBody></p:sp>{visual}</p:spTree></p:cSld></p:sld>'
        )

    @staticmethod
    def notes_xml():
        def shape(kind, text):
            type_attribute = f' type="{kind}"' if kind is not None else ""
            return (
                '<p:sp><p:nvSpPr><p:nvPr>'
                f'<p:ph{type_attribute}/></p:nvPr></p:nvSpPr>'
                f'<p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>'
            )
        return (
            '<p:notes xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<p:cSld><p:spTree>' + shape("body", "발표자 내장 노트")
            + shape("sldNum", "999") + shape("hdr", "머리말")
            + shape("ftr", "꼬리말") + shape("dt", "날짜")
            + shape(None, "종류 없는 자리표시자")
            + '</p:spTree></p:cSld></p:notes>'
        )

    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            capture_output=True, text=True, encoding="utf-8",
        )

    def test_extracts_actual_presentation_order_notes_and_markdown_lines(self):
        pptx = self.write_pptx()
        notes = self.root / "발표자노트.md"
        notes.write_text("# 발표 노트\n\n슬라이드와 자동 매핑하지 않음\n", encoding="utf-8")

        result = self.run_cli(pptx, "--notes", notes)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertLess(result.stdout.index("열째 한글"), result.stdout.index("첫째 & <escaped>"))
        self.assertIn("슬라이드 1", result.stdout)
        self.assertIn("part: ppt/slides/slide10.xml", result.stdout)
        self.assertIn("발표자 내장 노트", result.stdout)
        self.assertNotIn("머리말", result.stdout)
        self.assertNotIn("꼬리말", result.stdout)
        self.assertNotIn("999", result.stdout)
        self.assertNotIn("종류 없는 자리표시자", result.stdout)
        self.assertIn(f"{notes}:1: # 발표 노트", result.stdout)
        self.assertIn(f"{notes}:3: 슬라이드와 자동 매핑하지 않음", result.stdout)
        self.assertIn("자동으로 슬라이드에 매핑하지 않았습니다", result.stdout)
        self.assertIn(
            "텍스트 계층만 추출. 이미지·도형의 배치/화살표/차트 의미는 확인하지 않음",
            result.stdout,
        )

    def test_preserves_breaks_and_tabs_between_text_runs(self):
        pptx = self.write_pptx(order=("r1",), include_notes=False)
        with ZipFile(pptx, "r") as source:
            entries = {name: source.read(name) for name in source.namelist()}
        entries["ppt/slides/slide1.xml"] = (
            '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
            'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<p:cSld><p:spTree><p:sp><p:txBody><a:p>'
            '<a:r><a:t>첫 줄</a:t></a:r><a:br/>'
            '<a:r><a:t>둘째</a:t></a:r><a:tab/><a:r><a:t>열</a:t></a:r>'
            '</a:p></p:txBody></p:sp></p:spTree></p:cSld></p:sld>'
        ).encode("utf-8")
        with ZipFile(pptx, "w") as target:
            for name, data in entries.items():
                target.writestr(name, data)

        result = self.run_cli(pptx)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("첫 줄\n둘째\t열", result.stdout)

    def test_external_notes_are_optional(self):
        result = self.run_cli(self.write_pptx(include_notes=False))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("열째 한글", result.stdout)
        self.assertNotIn("외부 발표자 노트", result.stdout)

    def test_warns_for_non_text_and_textless_slide(self):
        pptx = self.write_pptx(order=("r1",), image_only=True)
        # Remove the text run while retaining the picture.
        with ZipFile(pptx, "r") as source:
            entries = {name: source.read(name) for name in source.namelist()}
        entries["ppt/slides/slide1.xml"] = self.slide_xml("", image=True).encode()
        with ZipFile(pptx, "w") as target:
            for name, data in entries.items():
                target.writestr(name, data)

        result = self.run_cli(pptx)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("경고: 텍스트가 없습니다", result.stdout)
        self.assertIn("이미지/도형/차트 등 비텍스트 요소", result.stdout)
        self.assertIn("OCR", result.stdout)

    def test_invalid_zip_missing_relationship_and_unsupported_formats_fail(self):
        invalid = self.root / "invalid.pptx"
        invalid.write_text("not a zip", encoding="utf-8")
        bad_rel = self.write_pptx("broken.pptx", missing_slide=True)
        ppt = self.root / "legacy.ppt"
        ppt.write_bytes(b"legacy")
        pdf = self.root / "slides.pdf"
        pdf.write_bytes(b"%PDF")

        for path, phrase in [
            (invalid, "유효한 PPTX ZIP"),
            (bad_rel, "찾을 수 없습니다"),
            (ppt, ".pptx만 지원"),
            (pdf, ".pptx만 지원"),
        ]:
            with self.subTest(path=path):
                result = self.run_cli(path)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(phrase, result.stderr)

    def test_output_write_preserves_source_and_refuses_collisions(self):
        pptx = self.write_pptx()
        before = hashlib.sha256(pptx.read_bytes()).digest()
        output = self.root / "추출.md"

        first = self.run_cli(pptx, "--output", output)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("열째 한글", output.read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(pptx.read_bytes()).digest(), before)

        output.write_text("보존할 내용", encoding="utf-8")
        second = self.run_cli(pptx, "--output", output)
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("이미 존재", second.stderr)
        self.assertEqual(output.read_text(encoding="utf-8"), "보존할 내용")

        same = self.run_cli(pptx, "--output", pptx)
        self.assertNotEqual(same.returncode, 0)
        self.assertIn("입력 PPTX와 달라야", same.stderr)
        self.assertEqual(hashlib.sha256(pptx.read_bytes()).digest(), before)

    def test_output_cannot_replace_external_notes(self):
        pptx = self.write_pptx()
        notes = self.root / "발표자노트.md"
        notes.write_text("보존할 프로젝트 발표 노트\n", encoding="utf-8")
        before = hashlib.sha256(notes.read_bytes()).digest()

        result = self.run_cli(pptx, "--notes", notes, "--output", notes)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("외부 발표자 노트와 달라야", result.stderr)
        self.assertEqual(hashlib.sha256(notes.read_bytes()).digest(), before)

    def test_rejects_relationship_target_escaping_archive(self):
        pptx = self.root / "escape.pptx"
        with ZipFile(pptx, "w") as archive:
            archive.writestr(
                "ppt/presentation.xml",
                f'<p:presentation xmlns:p="x" xmlns:r="{DOC_REL_NS}">'
                '<p:sldIdLst><p:sldId id="1" r:id="evil"/></p:sldIdLst>'
                '</p:presentation>',
            )
            archive.writestr(
                "ppt/_rels/presentation.xml.rels",
                f'<Relationships xmlns="{REL_NS}"><Relationship Id="evil" '
                f'Type="{DOC_REL_NS}/slide" Target="../../outside.xml"/>'
                '</Relationships>',
            )
        result = self.run_cli(pptx)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ZIP 루트 밖", result.stderr)

    def test_supports_package_root_relative_relationship_target(self):
        pptx = self.write_pptx(order=("r1",), include_notes=False)
        with ZipFile(pptx, "r") as source:
            entries = {name: source.read(name) for name in source.namelist()}
        entries["ppt/_rels/presentation.xml.rels"] = (
            f'<Relationships xmlns="{REL_NS}"><Relationship Id="r1" '
            f'Type="{DOC_REL_NS}/slide" Target="/ppt/slides/slide1.xml"/>'
            '</Relationships>'
        ).encode("utf-8")
        with ZipFile(pptx, "w") as target:
            for name, data in entries.items():
                target.writestr(name, data)

        result = self.run_cli(pptx)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("첫째 & <escaped>", result.stdout)

    def test_archive_open_oserror_and_encrypted_member_error_are_user_facing(self):
        from scripts import read_presentation

        pptx = self.write_pptx()
        with mock.patch.object(read_presentation, "ZipFile", side_effect=OSError("access denied")):
            with self.assertRaisesRegex(read_presentation.PresentationError, "열 수 없습니다"):
                read_presentation.extract_presentation(pptx)
        with mock.patch.object(read_presentation.ZipFile, "read",
                               side_effect=RuntimeError("encrypted")):
            with self.assertRaisesRegex(read_presentation.PresentationError, "읽을 수 없습니다"):
                read_presentation.extract_presentation(pptx)

    def test_rejects_external_slide_relationship_without_fetching(self):
        pptx = self.root / "external.pptx"
        with ZipFile(pptx, "w") as archive:
            archive.writestr(
                "ppt/presentation.xml",
                f'<p:presentation xmlns:p="x" xmlns:r="{DOC_REL_NS}">'
                '<p:sldIdLst><p:sldId id="1" r:id="remote"/></p:sldIdLst>'
                '</p:presentation>',
            )
            archive.writestr(
                "ppt/_rels/presentation.xml.rels",
                f'<Relationships xmlns="{REL_NS}"><Relationship Id="remote" '
                f'Type="{DOC_REL_NS}/slide" Target="https://example.invalid/slide.xml" '
                'TargetMode="External"/></Relationships>',
            )
        result = self.run_cli(pptx)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("외부 관계는 가져오지 않습니다", result.stderr)

    def test_malformed_xml_has_part_specific_error(self):
        pptx = self.root / "malformed.pptx"
        with ZipFile(pptx, "w") as archive:
            archive.writestr("ppt/presentation.xml", "<p:presentation>")
            archive.writestr("ppt/_rels/presentation.xml.rels", "<Relationships/>")
        result = self.run_cli(pptx)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("XML을 해석할 수 없습니다", result.stderr)
        self.assertIn("ppt/presentation.xml", result.stderr)


if __name__ == "__main__":
    unittest.main()
