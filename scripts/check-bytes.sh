#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

python3 - <<'PY'
from __future__ import annotations

import subprocess
import unicodedata
from collections import Counter
from pathlib import Path

ALLOWED_CONTROL_BYTES = {0x09, 0x0A, 0x0D}
PRIORITY_SUFFIXES = {".py": 0, ".md": 1}
CODE_TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".sh",
    ".toml",
    ".json",
    ".txt",
    ".yaml",
    ".yml",
}
COMMON_PUNCTUATION = set(
    r"""!"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"""
)
RECOMMENDED_EXTRA_CHARACTERS = {
    "·",
    "…",
    "“",
    "”",
    "‘",
    "’",
    "→",
}
RECOMMENDED_PATH_CHARACTERS = {"/", ".", "-", "_"}
INVISIBLE_CODEPOINTS = {
    0x00AD,  # soft hyphen
    0x034F,  # combining grapheme joiner
    0x061C,  # arabic letter mark
    0x115F,  # hangul choseong filler
    0x1160,  # hangul jungseong filler
    0x17B4,  # khmer vowel inherent aq
    0x17B5,  # khmer vowel inherent aa
    0x180E,  # mongolian vowel separator
    0x200B,  # zero width space
    0x200C,  # zero width non-joiner
    0x200D,  # zero width joiner
    0x200E,  # left-to-right mark
    0x200F,  # right-to-left mark
    0x2060,  # word joiner
    0x2061,  # function application
    0x2062,  # invisible times
    0x2063,  # invisible separator
    0x2064,  # invisible plus
    0x2066,  # left-to-right isolate
    0x2067,  # right-to-left isolate
    0x2068,  # first strong isolate
    0x2069,  # pop directional isolate
    0x206A,  # inhibit symmetric swapping
    0x206B,  # activate symmetric swapping
    0x206C,  # inhibit arabic form shaping
    0x206D,  # activate arabic form shaping
    0x206E,  # national digit shapes
    0x206F,  # nominal digit shapes
    0x3164,  # hangul filler
    0xFEFF,  # zero width no-break space / bom
    0xFFA0,  # halfwidth hangul filler
}
BIDI_CONTROL_CODEPOINTS = {
    0x061C,
    0x200E,
    0x200F,
    0x202A,
    0x202B,
    0x202C,
    0x202D,
    0x202E,
    0x2066,
    0x2067,
    0x2068,
    0x2069,
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
        text=False,
    )
    entries = [item for item in result.stdout.split(b"\x00") if item]
    return [Path(item.decode("utf-8")) for item in entries]


def prioritized_text_files(paths: list[Path]) -> list[Path]:
    text_files = [path for path in paths if path.suffix in CODE_TEXT_SUFFIXES]

    def sort_key(path: Path) -> tuple[int, str]:
        priority = PRIORITY_SUFFIXES.get(path.suffix, 9)
        return (priority, path.as_posix())

    return sorted(text_files, key=sort_key)


def find_disallowed_control_bytes(payload: bytes) -> list[tuple[int, int]]:
    issues: list[tuple[int, int]] = []
    for offset, value in enumerate(payload):
        if value == 0x00:
            issues.append((offset, value))
            continue
        if value == 0x7F:
            issues.append((offset, value))
            continue
        if value < 0x20 and value not in ALLOWED_CONTROL_BYTES:
            issues.append((offset, value))
    return issues


def is_hangul(char: str) -> bool:
    code = ord(char)
    return (
        0xAC00 <= code <= 0xD7A3
        or 0x1100 <= code <= 0x11FF
        or 0x3130 <= code <= 0x318F
        or 0xA960 <= code <= 0xA97F
        or 0xD7B0 <= code <= 0xD7FF
    )


def summarize_text(text: str) -> dict[str, int]:
    summary = {
        "ascii": 0,
        "digits": 0,
        "special": 0,
        "hangul_chars": 0,
        "hangul_bytes": 0,
    }

    for char in text:
        if char.isascii() and char.isalpha():
            summary["ascii"] += 1
        elif char.isascii() and char.isdigit():
            summary["digits"] += 1
        elif char in COMMON_PUNCTUATION:
            continue
        elif is_hangul(char):
            summary["hangul_chars"] += 1
            summary["hangul_bytes"] += len(char.encode("utf-8"))
        elif not char.isspace():
            summary["special"] += 1

    return summary


def included_text(summary: dict[str, int], key: str) -> str:
    return "Y" if summary[key] > 0 else "N"


def is_recommended_character(char: str) -> bool:
    if char.isspace():
        return True
    if char.isascii() and (char.isalpha() or char.isdigit() or char in COMMON_PUNCTUATION):
        return True
    if is_hangul(char):
        return True
    return char in RECOMMENDED_EXTRA_CHARACTERS


def recommended_deviation(text: str) -> tuple[int, list[str]]:
    counter: Counter[str] = Counter()
    for char in text:
        if is_recommended_character(char):
            continue
        counter[char] += 1

    samples = [
        f"{repr(char)} x{count} (U+{ord(char):04X})"
        for char, count in counter.most_common(5)
    ]
    return sum(counter.values()), samples


def is_recommended_path_character(char: str) -> bool:
    if is_recommended_character(char):
        return True
    return char in RECOMMENDED_PATH_CHARACTERS


def path_deviation(path: Path) -> tuple[int, list[str]]:
    counter: Counter[str] = Counter()
    path_text = path.as_posix()
    for char in path_text:
        if is_recommended_path_character(char):
            continue
        counter[char] += 1

    samples = [
        f"{repr(char)} x{count} (U+{ord(char):04X})"
        for char, count in counter.most_common(5)
    ]
    return sum(counter.values()), samples


def line_column(text: str, index: int) -> tuple[int, int]:
    line = text.count("\n", 0, index) + 1
    last_newline = text.rfind("\n", 0, index)
    if last_newline == -1:
        column = index + 1
    else:
        column = index - last_newline
    return line, column


def find_invisible_or_bidi_characters(
    text: str,
) -> tuple[list[str], list[str]]:
    invisible_warnings: list[str] = []
    bidi_warnings: list[str] = []
    for index, char in enumerate(text):
        codepoint = ord(char)
        if codepoint in INVISIBLE_CODEPOINTS:
            line, column = line_column(text, index)
            invisible_warnings.append(
                f"line={line} col={column} char=U+{codepoint:04X} "
                f"name={unicodedata.name(char, 'UNKNOWN')}"
            )
        if codepoint in BIDI_CONTROL_CODEPOINTS:
            line, column = line_column(text, index)
            bidi_warnings.append(
                f"line={line} col={column} char=U+{codepoint:04X} "
                f"name={unicodedata.name(char, 'UNKNOWN')}"
            )
    return invisible_warnings, bidi_warnings


def find_ascii_hidden_warnings(text: str) -> list[str]:
    warnings: list[str] = []
    for index, char in enumerate(text):
        if char not in {"\t", "\r"}:
            continue
        line, column = line_column(text, index)
        label = "TAB" if char == "\t" else "CR"
        warnings.append(
            f"line={line} col={column} ascii-hidden={label} "
            f"char=U+{ord(char):04X}"
        )
    return warnings


def normalization_warning(text: str) -> str | None:
    normalized_nfc = unicodedata.normalize("NFC", text)
    normalized_nfkc = unicodedata.normalize("NFKC", text)
    if text == normalized_nfc and text == normalized_nfkc:
        return None

    details: list[str] = []
    if text != normalized_nfc:
        details.append("differs_from_nfc")
    if text != normalized_nfkc:
        details.append("differs_from_nfkc")
    return ", ".join(details)


def main() -> int:
    failures: list[str] = []
    warnings: list[str] = []
    totals = {
        "ascii": 0,
        "digits": 0,
        "special": 0,
        "hangul_chars": 0,
        "hangul_bytes": 0,
    }

    tracked = tracked_files()
    prioritized = prioritized_text_files(tracked)
    per_file: list[tuple[Path, dict[str, int]]] = []

    for path in prioritized:
        if not path.is_file():
            continue

        path_deviation_count, path_deviation_samples = path_deviation(path)
        if path_deviation_count > 0:
            preview = ", ".join(path_deviation_samples)
            warnings.append(
                f"{path}: path/filename recommended range deviation "
                f"count={path_deviation_count} sample=[{preview}]"
            )

        payload = path.read_bytes()
        control_issues = find_disallowed_control_bytes(payload)
        if control_issues:
            preview = ", ".join(
                f"offset={offset} byte=0x{value:02x}"
                for offset, value in control_issues[:10]
            )
            failures.append(f"{path}: disallowed control bytes ({preview})")
            continue

        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            failures.append(
                f"{path}: invalid utf-8 at bytes {exc.start}-{exc.end}: {exc.reason}"
            )
            continue

        invisible_warnings, bidi_warnings = find_invisible_or_bidi_characters(text)
        if invisible_warnings:
            warnings.append(
                f"{path}: invisible/unreadable unicode sample=["
                + ", ".join(invisible_warnings[:5])
                + "]"
            )
        if bidi_warnings:
            warnings.append(
                f"{path}: bidi control unicode sample=["
                + ", ".join(bidi_warnings[:5])
                + "]"
            )

        ascii_hidden_warnings = find_ascii_hidden_warnings(text)
        if ascii_hidden_warnings:
            warnings.append(
                f"{path}: ascii hidden character sample=["
                + ", ".join(ascii_hidden_warnings[:5])
                + "]"
            )

        normalization_issue = normalization_warning(text)
        if normalization_issue is not None:
            warnings.append(
                f"{path}: normalization warning [{normalization_issue}]"
            )

        summary = summarize_text(text)
        per_file.append((path, summary))
        for key, value in summary.items():
            totals[key] += value

        deviation_count, deviation_samples = recommended_deviation(text)
        if deviation_count > 0:
            preview = ", ".join(deviation_samples)
            warnings.append(
                f"{path}: recommended range deviation count={deviation_count} "
                f"sample=[{preview}]"
            )

    if failures:
        print("[byte-check] non-human-readable bytes detected:")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("[byte-check] OK: tracked files contain readable utf-8 text bytes only.")
    print("[byte-check] tracked text/code files:")
    for path, summary in per_file:
        print(
            " - "
            f"{path} "
            f"(ascii={included_text(summary, 'ascii')}, "
            f"digits={included_text(summary, 'digits')}, "
            f"special={included_text(summary, 'special')}, "
            f"hangul={included_text(summary, 'hangul_chars')})"
        )
    print(
        "[byte-check] summary: "
        f"ascii={totals['ascii']} "
        f"digits={totals['digits']} "
        f"special={totals['special']} "
        f"hangul_chars={totals['hangul_chars']} "
        f"hangul_bytes={totals['hangul_bytes']}"
    )
    if warnings:
        print("[byte-check] recommended range deviations:")
        for warning in warnings:
            print(f" - {warning}")
    return 0


raise SystemExit(main())
PY
