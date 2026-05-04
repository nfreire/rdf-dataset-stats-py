"""Command-line entry point for RDF dataset statistics."""

from __future__ import annotations

import argparse
import logging
import math
import sys
from pathlib import Path
from typing import Sequence

from rdf_dataset_stats.collector import collect_dump_stats
from rdf_dataset_stats.excel import write_excel


def main(argv: Sequence[str] | None = None) -> int:
    """Run the RDF dataset statistics command-line interface."""
    _suppress_noisy_rdflib_warnings()
    parser = _build_parser()
    args = parser.parse_args(argv)

    input_path, output_path = _resolve_paths(parser, args)
    if input_path is None or output_path is None:
        return 2

    if not input_path.is_dir():
        print(f"Error: input path is not a directory: {input_path}", file=sys.stderr)
        return 1

    try:
        stats, processed_records = collect_dump_stats(
            input_path,
            on_subdataset=_print_subdataset,
            on_progress=_print_progress,
        )
        write_excel(stats, output_path)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Processed records: {processed_records}")
    print(f"Classes found: {len(stats)}")
    print(f"Output written to: {output_path}")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rdf-dataset-stats",
        description="Collect RDF class and property statistics from a dataset dump.",
    )
    parser.add_argument("input_path", nargs="?", help="RDF dump input folder")
    parser.add_argument("output_path", nargs="?", help="Output .xlsx file path")
    parser.add_argument("--input", dest="input_option", help="RDF dump input folder")
    parser.add_argument("--output", dest="output_option", help="Output .xlsx file path")
    return parser


def _resolve_paths(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> tuple[Path | None, Path | None]:
    input_value = args.input_option or args.input_path
    output_value = args.output_option or args.output_path

    if args.input_option and args.input_path:
        parser.error("input path cannot be provided both positionally and with --input")
    if args.output_option and args.output_path:
        parser.error("output path cannot be provided both positionally and with --output")
    if bool(input_value) != bool(output_value):
        parser.error("both input and output paths are required")
    if not input_value or not output_value:
        parser.error("input and output paths are required")

    return Path(input_value), Path(output_value)


def _print_subdataset(subdataset: str) -> None:
    print(f"Processing subdataset: {subdataset}")


def _print_progress(
    processed_records: int, records_per_second: float, seconds_per_million: float
) -> None:
    print(f"Records processed so far: {processed_records}")
    print(f"Average records per second: {records_per_second:.2f}")
    print(
        "Estimated time for 1000000 records: "
        f"{_format_duration(seconds_per_million)}"
    )


def _format_duration(seconds: float) -> str:
    if not math.isfinite(seconds) or seconds < 0:
        return "00:00:00"

    total_seconds = int(round(seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _suppress_noisy_rdflib_warnings() -> None:
    logging.getLogger("rdflib.term").setLevel(logging.CRITICAL)


if __name__ == "__main__":
    raise SystemExit(main())
