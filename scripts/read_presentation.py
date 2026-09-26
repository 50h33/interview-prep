"""Extract auditable text from a PPTX and an optional Markdown speaker note.

This intentionally does not perform OCR or interpret images, charts, diagrams,
connectors, or their spatial meaning. It reads only OOXML text runs and the
body placeholder of an embedded notes slide.
"""

import argparse
from pathlib import Path, PurePosixPath
import posixpath
import sys
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile


PRESENTATION_PART = "ppt/presentation.xml"
PRESENTATION_RELS = "ppt/_rels/presentation.xml.rels"
VISUAL_ELEMENTS = {"pic", "graphicFrame", "cxnSp"}
SYSTEM_NOTE_PLACEHOLDERS = {"sldNum", "hdr", "ftr", "dt", "sldImg"}


class PresentationError(Exception):
    """A user-facing failure caused by an unsupported or damaged input."""


def local_name(tag):
    """Return an XML local name for transitional and strict OOXML alike."""
    return tag.rsplit("}", 1)[-1]


def parse_xml(data, part):
    try:
        return ElementTree.fromstring(data)
    except ElementTree.ParseError as error:
        raise PresentationError(f"XML을 해석할 수 없습니다: {part}: {error}") from error


def read_part(archive, part):
    try:
        return archive.read(part)
    except KeyError as error:
        raise PresentationError(f"PPTX 안에서 필요한 part를 찾을 수 없습니다: {part}") from error
    except (BadZipFile, OSError, RuntimeError) as error:
        raise PresentationError(f"PPTX ZIP 항목을 읽을 수 없습니다: {part}: {error}") from error


def relationship_id(element):
    """Read r:id without confusing it with the numeric, unqualified id."""
    for name, value in element.attrib.items():
        if name.startswith("{") and local_name(name) == "id":
            return value
    return None


def read_relationships(archive, rels_part, *, required=True):
    if rels_part not in archive.namelist():
        if required:
            raise PresentationError(
                f"PPTX 안에서 관계 파일을 찾을 수 없습니다: {rels_part}"
            )
        return {}
    root = parse_xml(read_part(archive, rels_part), rels_part)
    relationships = {}
    for element in root.iter():
        if local_name(element.tag) != "Relationship":
            continue
        rel_id = element.get("Id")
        if rel_id:
            relationships[rel_id] = {
                "target": element.get("Target", ""),
                "type": element.get("Type", ""),
                "mode": element.get("TargetMode", ""),
            }
    return relationships


def resolve_target(source_part, target):
    """Resolve an internal relationship target without leaving the ZIP root."""
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        raise PresentationError(f"외부 관계 target은 읽지 않습니다: {target}")
    decoded = unquote(parsed.path)
    if not decoded or decoded.startswith("//") or "\\" in decoded:
        raise PresentationError(f"유효한 상대 POSIX 관계 target이 아닙니다: {target}")
    if decoded.startswith("/"):
        resolved = posixpath.normpath(decoded[1:])
    else:
        resolved = posixpath.normpath(
            posixpath.join(posixpath.dirname(source_part), decoded)
        )
    if resolved == ".." or resolved.startswith("../") or resolved.startswith("/"):
        raise PresentationError(f"관계 target이 ZIP 루트 밖을 가리킵니다: {target}")
    # PurePosixPath also rejects accidental platform-specific interpretation.
    return PurePosixPath(resolved).as_posix()


def relationship_target(source_part, rel_id, relationship):
    if relationship.get("mode", "").lower() == "external":
        raise PresentationError(f"외부 관계는 가져오지 않습니다: {rel_id}")
    return resolve_target(source_part, relationship.get("target", ""))


def text_from_tree(root):
    """Extract a:t strings, preserving paragraph boundaries and run order."""
    paragraphs = []
    for paragraph in root.iter():
        if local_name(paragraph.tag) != "p":
            continue
        fragments = []
        for node in paragraph.iter():
            name = local_name(node.tag)
            if name == "t":
                fragments.append(node.text or "")
            elif name == "br":
                fragments.append("\n")
            elif name == "tab":
                fragments.append("\t")
        text = "".join(fragments)
        if text:
            paragraphs.append(text)
    return "\n".join(paragraphs)


def has_visual_content(root):
    return any(local_name(element.tag) in VISUAL_ELEMENTS for element in root.iter())


def relationships_part(part):
    path = PurePosixPath(part)
    return (path.parent / "_rels" / (path.name + ".rels")).as_posix()


def embedded_notes(archive, slide_part):
    rels = read_relationships(archive, relationships_part(slide_part), required=False)
    notes_rel = next(
        (relationship for relationship in rels.values()
         if relationship.get("type", "").rstrip("/").endswith("/notesSlide")),
        None,
    )
    if notes_rel is None:
        return None
    notes_part = relationship_target(slide_part, "notesSlide", notes_rel)
    notes_root = parse_xml(read_part(archive, notes_part), notes_part)
    bodies = []
    for shape in notes_root.iter():
        if local_name(shape.tag) != "sp":
            continue
        placeholders = [element for element in shape.iter()
                        if local_name(element.tag) == "ph"]
        if not placeholders:
            continue
        placeholder_type = placeholders[0].get("type")
        if placeholder_type in SYSTEM_NOTE_PLACEHOLDERS or placeholder_type != "body":
            continue
        text = text_from_tree(shape)
        if text:
            bodies.append(text)
    return "\n".join(bodies) or None


def extract_presentation(path):
    try:
        with ZipFile(path, "r") as archive:
            presentation = parse_xml(
                read_part(archive, PRESENTATION_PART), PRESENTATION_PART
            )
            relationships = read_relationships(archive, PRESENTATION_RELS)
            slide_ids = [element for element in presentation.iter()
                         if local_name(element.tag) == "sldId"]
            if not slide_ids:
                raise PresentationError("presentation.xml에 슬라이드 목록이 없습니다")

            slides = []
            for number, slide_id in enumerate(slide_ids, start=1):
                rel_id = relationship_id(slide_id)
                if not rel_id:
                    raise PresentationError(
                        f"슬라이드 {number}에 관계 ID(r:id)가 없습니다"
                    )
                relationship = relationships.get(rel_id)
                if relationship is None:
                    raise PresentationError(
                        f"슬라이드 {number}의 관계를 찾을 수 없습니다: {rel_id}"
                    )
                if not relationship.get("type", "").rstrip("/").endswith("/slide"):
                    raise PresentationError(
                        f"슬라이드 {number}의 관계가 slide 관계가 아닙니다: {rel_id}"
                    )
                part = relationship_target(PRESENTATION_PART, rel_id, relationship)
                slide_root = parse_xml(read_part(archive, part), part)
                slides.append({
                    "number": number,
                    "part": part,
                    "text": text_from_tree(slide_root),
                    "notes": embedded_notes(archive, part),
                    "has_visual": has_visual_content(slide_root),
                })
            return slides
    except BadZipFile as error:
        raise PresentationError(f"유효한 PPTX ZIP 파일이 아닙니다: {path}") from error
    except OSError as error:
        raise PresentationError(f"PPTX 파일을 열 수 없습니다: {path}: {error}") from error
    except RuntimeError as error:
        raise PresentationError(f"PPTX 파일을 읽을 수 없습니다: {path}: {error}") from error


def read_external_notes(path):
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise PresentationError(f"외부 발표자 노트를 읽을 수 없습니다: {path}: {error}") from error
    return [f"{path}:{number}: {line}" for number, line in enumerate(text.splitlines(), 1)]


def render(source, slides, notes_path=None):
    lines = [
        "# 발표 자료 텍스트 추출",
        "",
        "- 텍스트 계층만 추출. 이미지·도형의 배치/화살표/차트 의미는 확인하지 않음",
        f"- 원본: {source}",
    ]
    for slide in slides:
        lines.extend(["", f"## 슬라이드 {slide['number']}", "",
                      f"- part: {slide['part']}", "", "### 텍스트", ""])
        if slide["text"]:
            lines.append(slide["text"])
        else:
            lines.append("- 경고: 텍스트가 없습니다.")
        if slide["has_visual"]:
            lines.extend([
                "",
                "- 경고: 이미지/도형/차트 등 비텍스트 요소가 있습니다. "
                "OCR이나 그래프·화살표의 의미 해석은 수행하지 않았습니다.",
            ])
        if slide["notes"]:
            lines.extend(["", "### 내장 발표자 노트", "", slide["notes"]])

    if notes_path is not None:
        lines.extend([
            "", "## 외부 발표자 노트", "",
            "> 외부 노트는 자동으로 슬라이드에 매핑하지 않았습니다.", "",
            *read_external_notes(notes_path),
        ])
    return "\n".join(lines) + "\n"


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path, help="읽을 .pptx 파일")
    parser.add_argument("--notes", type=Path, help="별도로 작성한 UTF-8 Markdown 노트")
    parser.add_argument("--output", type=Path, help="stdout 대신 새 UTF-8 파일에 저장")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.pptx.suffix.lower() != ".pptx":
            raise PresentationError("지원하지 않는 형식입니다. .pptx만 지원하며 .ppt/.pdf는 읽지 않습니다")
        if not args.pptx.is_file():
            raise PresentationError(f"입력 PPTX 파일을 찾을 수 없습니다: {args.pptx}")
        if args.notes is not None and not args.notes.is_file():
            raise PresentationError(f"외부 발표자 노트 파일을 찾을 수 없습니다: {args.notes}")
        if args.output is not None and args.output.resolve() == args.pptx.resolve():
            raise PresentationError("출력 경로는 입력 PPTX와 달라야 합니다")
        if (args.output is not None and args.notes is not None
                and args.output.resolve() == args.notes.resolve()):
            raise PresentationError("출력 경로는 외부 발표자 노트와 달라야 합니다")

        rendered = render(args.pptx, extract_presentation(args.pptx), args.notes)
        if args.output is None:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8")
            sys.stdout.write(rendered)
        else:
            try:
                with args.output.open("x", encoding="utf-8", newline="\n") as output:
                    output.write(rendered)
            except FileExistsError as error:
                raise PresentationError(
                    f"출력 파일이 이미 존재하여 덮어쓰지 않았습니다: {args.output}"
                ) from error
            except OSError as error:
                raise PresentationError(f"출력 파일을 쓸 수 없습니다: {args.output}: {error}") from error
    except PresentationError as error:
        build_parser().exit(1, f"Error: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
