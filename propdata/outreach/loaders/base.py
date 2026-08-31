"""Loading organisations from public business registers.

Mirrors the property `Source` contract, but produces `Organisation` rather
than `Property` — different pipeline, same shape: fetch, parse, normalise.

One rule holds across every loader here, and it is the reason the module
exists rather than the records being typed in: **legal form must be evidenced,
never inferred from a name.** "Smith Estates Ltd" almost certainly is a
limited company, and almost certainly is not good enough. Under PECR the legal
form decides whether marketing email may be sent without consent, so a wrong
guess in the corporate direction is an unlawful send. A loader that cannot
evidence the form sets `LegalForm.UNKNOWN`, which the compliance gate treats
as non-corporate.
"""

from __future__ import annotations

import csv
import io
import zipfile
from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from propdata.outreach.models import Organisation


def normalise_header(name: str) -> str:
    """Lowercase, underscore-separated form of a CSV header cell.

    Registers are inconsistent about case, spacing, dots and BOMs across
    releases; normalising once means the alias tables below stay readable.
    """
    cleaned = (name or "").strip().lstrip("﻿").lower()
    for character in (" ", ".", "-", "/"):
        cleaned = cleaned.replace(character, "_")
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")


def pick(row: dict[str, str], *aliases: str) -> str | None:
    """First non-empty value among `aliases`.

    Register column names drift between publications. Listing the aliases
    keeps a loader working across releases instead of failing on a rename.
    """
    for alias in aliases:
        value = (row.get(alias) or "").strip()
        if value:
            return value
    return None


def read_csv_rows(content: bytes) -> Iterator[dict[str, str]]:
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        yield {normalise_header(k): (v or "") for k, v in row.items() if k is not None}


def read_files(path: str | Path, suffixes: tuple[str, ...]) -> Iterator[bytes]:
    """Yield file contents from a file, a directory, or a zip archive."""
    target = Path(path).expanduser().resolve()
    if not target.exists():
        raise FileNotFoundError(target)

    if target.is_dir():
        files = sorted(
            f for f in target.rglob("*") if f.is_file() and f.suffix.lower() in suffixes
        )
        if not files:
            raise FileNotFoundError(f"no {'/'.join(suffixes)} files under {target}")
        for file in files:
            yield file.read_bytes()
    elif target.suffix.lower() == ".zip":
        with zipfile.ZipFile(target) as archive:
            for name in archive.namelist():
                if Path(name).suffix.lower() in suffixes:
                    yield archive.read(name)
    else:
        yield target.read_bytes()


class OrganisationSource(ABC):
    id: str
    country: str
    licence: str
    notes: str = ""
    #: True when this register evidences legal form. False means every
    #: organisation it yields is UNKNOWN and will be blocked from electronic
    #: marketing until matched against a register that does.
    evidences_legal_form: bool = False

    @abstractmethod
    def load(self, path: str | Path, **options: Any) -> Iterator[Organisation]:
        """Yield organisations from a local copy of the register."""

    def load_all(self, path: str | Path, **options: Any) -> list[Organisation]:
        return list(self.load(path, **options))


def deduplicate(organisations: Iterable[Organisation]) -> list[Organisation]:
    """Collapse organisations sharing an org_id, keeping the first seen."""
    seen: dict[str, Organisation] = {}
    for org in organisations:
        seen.setdefault(org.org_id, org)
    return list(seen.values())
