from dataclasses import dataclass
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest
from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF

from rdf_dataset_stats import collector


EX = "http://example.org/"


@dataclass
class FakeRecord:
    graph: Graph
    subdataset: str | None = None


class FakeRDFDumpReader:
    calls: list[tuple[object, str, str]] = []
    records: list[FakeRecord] = []

    def __init__(
        self, input_path: object, on_parse_error: str, invalid_uri_policy: str
    ) -> None:
        self.calls.append((input_path, on_parse_error, invalid_uri_policy))

    def __iter__(self):
        return iter(self.records)


def make_graph(class_name: str, title: str) -> Graph:
    graph = Graph()
    subject = URIRef(f"{EX}{title}")
    graph.add((subject, RDF.type, URIRef(f"{EX}{class_name}")))
    graph.add((subject, URIRef(f"{EX}title"), Literal(title)))
    return graph


def test_collect_dump_stats_uses_rdf_dump_reader_with_expected_options(
    monkeypatch,
) -> None:
    FakeRDFDumpReader.calls = []
    FakeRDFDumpReader.records = []
    monkeypatch.setitem(
        __import__("sys").modules,
        "rdf_dump_reader",
        SimpleNamespace(RDFDumpReader=FakeRDFDumpReader),
    )
    input_path = Path("dump-folder")

    collector.collect_dump_stats(input_path)

    assert FakeRDFDumpReader.calls == [
        (input_path, "skip_record", "keep"),
    ]


def test_collect_dump_stats_processes_each_record_graph(monkeypatch) -> None:
    FakeRDFDumpReader.calls = []
    FakeRDFDumpReader.records = [
        FakeRecord(make_graph("ClassA", "First")),
        FakeRecord(make_graph("ClassB", "Second")),
    ]
    monkeypatch.setitem(
        __import__("sys").modules,
        "rdf_dump_reader",
        SimpleNamespace(RDFDumpReader=FakeRDFDumpReader),
    )

    stats, processed_records = collector.collect_dump_stats("dump-folder")

    assert processed_records == 2
    assert stats[f"{EX}ClassA"].class_count == 1
    assert stats[f"{EX}ClassB"].class_count == 1
    assert stats[f"{EX}ClassA"].properties[f"{EX}title"].literal_count == 1
    assert stats[f"{EX}ClassB"].properties[f"{EX}title"].literal_count == 1


def test_collect_dump_stats_reports_subdataset_changes(monkeypatch) -> None:
    FakeRDFDumpReader.calls = []
    FakeRDFDumpReader.records = [
        FakeRecord(make_graph("ClassA", "First"), subdataset="00719"),
        FakeRecord(make_graph("ClassA", "Second"), subdataset="00719"),
        FakeRecord(make_graph("ClassB", "Third"), subdataset="00725"),
    ]
    monkeypatch.setitem(
        __import__("sys").modules,
        "rdf_dump_reader",
        SimpleNamespace(RDFDumpReader=FakeRDFDumpReader),
    )
    reported_subdatasets: list[str] = []

    collector.collect_dump_stats(
        "dump-folder",
        on_subdataset=reported_subdatasets.append,
    )

    assert reported_subdatasets == ["00719", "00725"]


def test_collect_dump_stats_reports_periodic_progress(monkeypatch) -> None:
    FakeRDFDumpReader.calls = []
    FakeRDFDumpReader.records = [
        FakeRecord(make_graph("ClassA", "First"), subdataset="00719"),
        FakeRecord(make_graph("ClassA", "Second"), subdataset="00719"),
        FakeRecord(make_graph("ClassB", "Third"), subdataset="00725"),
    ]
    monkeypatch.setitem(
        __import__("sys").modules,
        "rdf_dump_reader",
        SimpleNamespace(RDFDumpReader=FakeRDFDumpReader),
    )
    times = iter([0.0, 100.0, 300.0, 301.0])
    progress_updates: list[tuple[int, float, float]] = []

    collector.collect_dump_stats(
        "dump-folder",
        on_progress=lambda processed, rate, estimate: progress_updates.append(
            (processed, rate, estimate)
        ),
        clock=lambda: next(times),
    )

    assert progress_updates == [
        (2, 2 / 300, 150_000_000.0),
    ]


def test_collect_dump_stats_reports_intermediate_results(monkeypatch) -> None:
    FakeRDFDumpReader.calls = []
    FakeRDFDumpReader.records = [
        FakeRecord(make_graph("ClassA", "First"), subdataset="00719"),
        FakeRecord(make_graph("ClassA", "Second"), subdataset="00719"),
        FakeRecord(make_graph("ClassB", "Third"), subdataset="00725"),
    ]
    monkeypatch.setitem(
        __import__("sys").modules,
        "rdf_dump_reader",
        SimpleNamespace(RDFDumpReader=FakeRDFDumpReader),
    )
    intermediate_results: list[tuple[int, int]] = []

    collector.collect_dump_stats(
        "dump-folder",
        on_intermediate_result=lambda stats, processed: intermediate_results.append(
            (processed, stats[f"{EX}ClassA"].class_count)
        ),
        intermediate_record_interval=2,
    )

    assert intermediate_results == [(2, 2)]


def test_collect_dump_stats_reads_real_fixture_dump(caplog) -> None:
    rdf_dump_reader = pytest.importorskip("rdf_dump_reader")
    if not hasattr(rdf_dump_reader, "RDFDumpReader"):
        pytest.skip("rdf_dump_reader.RDFDumpReader is not importable")
    caplog.set_level(logging.CRITICAL)

    stats, processed_records = collector.collect_dump_stats(Path("tests/data"))

    assert processed_records == 106
    assert len(stats) == 8
    assert (
        stats["http://www.europeana.eu/schemas/edm/EuropeanaAggregation"].class_count
        == 106
    )
    assert (
        stats["http://www.openarchives.org/ore/terms/Proxy"].class_count == 212
    )
    assert (
        len(
            stats[
                "http://www.openarchives.org/ore/terms/Proxy"
            ].properties
        )
        == 17
    )
