#!/usr/bin/env python3
"""Publish the one-star review entry for the make.fun bounty
"One-Star Review of Something Essential".

The entry lives in ``entry.txt`` next to this file: one single-line,
deadpan one-star review, at most 160 characters, of an everyday
essential everyone relies on — here, gravity, reviewed as a faulty
product that cannot be returned. The joke is deadpan throughout: a
real complaint filed in earnest against a thing that cannot be
fixed, landing in one line and turning in the last few words.

This program reads the entry's exact bytes, runs every gate check
and every register check on them, publishes the raw bytes verbatim
to ``entry.txt`` in the output directory, and reads the published
file back to confirm the bytes match the source exactly, so the
judge sees precisely the text that was written here.

The output directory is ``$MAKEFUN_OUTPUT_DIR`` when set, else
``/output``. Pass ``--output-dir <dir>`` to choose it on the command
line instead, ``--verify-only`` to check the entry without writing
anything, or ``--show`` to print the entry and its gate report.
Standard library only: no network access, no clock reads, no
randomness, so two runs always produce identical output.
"""

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_CHARS = 160
ENTRY_NAME = "entry.txt"
# Everyday essentials the review may complain about, per the brief.
ESSENTIALS = (
    "sun", "gravity", "sleep", "water", "oxygen", "monday",
    "mondays", "air", "rain", "time", "coffee",
)


@dataclass
class GateReport:
    """Everything the bounty gate measures about one entry."""

    characters: int
    characters_left: int
    words: int
    byte_length: int

    @classmethod
    def measure(cls, text: str, raw: bytes) -> "GateReport":
        return cls(
            characters=len(text),
            characters_left=MAX_CHARS - len(text),
            words=len(text.split()),
            byte_length=len(raw),
        )

    def describe(self) -> str:
        return (
            f"{self.characters} characters "
            f"({self.characters_left} of {MAX_CHARS} left), "
            f"{self.words} words, {self.byte_length} bytes"
        )


class Gate:
    """One named check per rule, so a failure names exactly what broke."""

    def __init__(self, text: str):
        self.text = text

    def check_not_empty(self) -> str | None:
        if not self.text or self.text.isspace():
            return "entry is empty or only white space"
        return None

    def check_length(self) -> str | None:
        if len(self.text) > MAX_CHARS:
            return (
                f"entry is {len(self.text)} characters, "
                f"over the {MAX_CHARS} limit"
            )
        return None

    def check_single_line(self) -> str | None:
        if "\n" in self.text or "\r" in self.text:
            return "entry must be a single line"
        return None

    def check_no_edge_space(self) -> str | None:
        if self.text != self.text.strip():
            return "entry must not start or end with white space"
        return None

    def check_star_rating(self) -> str | None:
        """The review must open by stating its one-star rating."""
        if not self.text.lower().startswith("one star"):
            return "entry must open with its one-star rating"
        return None

    def check_names_essential(self) -> str | None:
        """The complaint must be about an everyday essential."""
        lowered = self.text.lower()
        if not any(word in lowered for word in ESSENTIALS):
            return "entry must name an everyday essential"
        return None

    def check_deadpan(self) -> str | None:
        """Deadpan holds: no exclamation marks, no shouting."""
        if "!" in self.text:
            return "entry must stay deadpan: no exclamation marks"
        return None

    def problems(self) -> list[str]:
        checks = (
            self.check_not_empty,
            self.check_length,
            self.check_single_line,
            self.check_no_edge_space,
            self.check_star_rating,
            self.check_names_essential,
            self.check_deadpan,
        )
        return [p for check in checks if (p := check()) is not None]


def load_entry(source_dir: Path) -> tuple[bytes, str, GateReport]:
    """Read the entry bytes, decode them, and run every check."""
    source = source_dir / ENTRY_NAME
    if not source.is_file():
        raise SystemExit(f"entry file missing: {source}")
    raw = source.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SystemExit(f"entry is not valid UTF-8: {exc}") from exc
    problems = Gate(text).problems()
    if problems:
        raise SystemExit("; ".join(problems))
    return raw, text, GateReport.measure(text, raw)


def resolve_output_dir(cli_dir: str | None) -> Path:
    """Pick the output directory: flag first, then env, then /output."""
    if cli_dir:
        return Path(cli_dir)
    if env_dir := os.environ.get("MAKEFUN_OUTPUT_DIR"):
        return Path(env_dir)
    return Path("/output")


def publish(raw: bytes, out_dir: Path) -> Path:
    """Write the raw entry bytes verbatim and verify them by re-reading."""
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / ENTRY_NAME
    target.write_bytes(raw)
    published = target.read_bytes()
    if published != raw:
        raise SystemExit("published entry does not match entry.txt")
    if len(published) != len(raw):
        raise SystemExit("published entry byte length differs")
    return target


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=None,
        help="directory to write entry.txt into",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="validate the entry without writing anything",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="print the entry and its gate report",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    here = Path(__file__).resolve().parent
    raw, text, report = load_entry(here)
    if args.show:
        print(text)
        print(f"Gate: {report.describe()}")
    if args.verify_only:
        print(f"Valid: {report.describe()}")
        return 0
    target = publish(raw, resolve_output_dir(args.output_dir))
    print(f"Wrote {report.describe()} to {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
