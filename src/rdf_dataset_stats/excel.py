"""Excel workbook output."""

from __future__ import annotations

import re
from pathlib import Path

from openpyxl import Workbook

from rdf_dataset_stats.model import DatasetStats

INVALID_SHEET_NAME_CHARS = re.compile(r"[:\\/?*\[\]]")
MAX_SHEET_NAME_LENGTH = 31


def safe_sheet_name(class_uri: str, used_names: set[str]) -> str:
    """Return a valid, unique Excel sheet name for an RDF class URI."""
    name = _shorten_uri(class_uri)
    name = INVALID_SHEET_NAME_CHARS.sub("_", name).strip()
    if not name:
        name = "Class"

    base_name = name[:MAX_SHEET_NAME_LENGTH]
    candidate = base_name
    suffix_number = 2

    while candidate in used_names:
        suffix = f"_{suffix_number}"
        available_length = MAX_SHEET_NAME_LENGTH - len(suffix)
        candidate = f"{base_name[:available_length]}{suffix}"
        suffix_number += 1

    used_names.add(candidate)
    return candidate


def write_excel(stats: DatasetStats, output_path: str | Path) -> None:
    """Write dataset statistics to an Excel workbook."""
    workbook = Workbook()
    default_sheet = workbook.active
    used_sheet_names: set[str] = set()

    if len(stats) == 0:
        default_sheet.title = "Statistics"
    else:
        workbook.remove(default_sheet)

    for class_uri, class_stats in stats.sorted_classes():
        sheet = workbook.create_sheet(
            title=safe_sheet_name(class_uri, used_sheet_names)
        )
        sheet.append(["Class URI:", class_uri])
        sheet.append(["Class count:", class_stats.class_count])
        sheet.append([])
        sheet.append(
            [
                "Property URI",
                "Literal count",
                "Resource object class URI",
                "Resource count",
            ]
        )

        for property_uri, property_stats in class_stats.sorted_properties():
            sheet.append([property_uri, property_stats.literal_count, None, None])
            for object_class_uri, count in property_stats.resource_counts.sorted_items():
                sheet.append([property_uri, None, object_class_uri, count])

    workbook.save(output_path)


def _shorten_uri(uri: str) -> str:
    trimmed_uri = uri.rstrip("#/")
    if "#" in trimmed_uri:
        return trimmed_uri.rsplit("#", 1)[1]
    if "/" in trimmed_uri:
        return trimmed_uri.rsplit("/", 1)[1]
    return trimmed_uri
