"""RDF graph statistics collection."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from time import monotonic

from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS

from rdf_dataset_stats.model import DatasetStats


def collect_graph_stats(graph: Graph, stats: DatasetStats) -> None:
    """Collect aggregate statistics from one RDF record graph."""
    subject_classes: dict[URIRef | BNode, list[str]] = {}

    for subject, _, class_term in graph.triples((None, RDF.type, None)):
        class_uri = str(class_term)
        stats.increment_class(class_uri)
        if isinstance(subject, URIRef | BNode):
            subject_classes.setdefault(subject, []).append(class_uri)

    for subject, class_uris in subject_classes.items():
        for _, predicate, object_term in graph.triples((subject, None, None)):
            if predicate == RDF.type:
                continue

            property_uri = str(predicate)
            if isinstance(object_term, Literal):
                for class_uri in class_uris:
                    stats.increment_literal_property(class_uri, property_uri)
            elif isinstance(object_term, URIRef | BNode):
                object_classes = [
                    str(object_class)
                    for object_class in graph.objects(object_term, RDF.type)
                ]
                if not object_classes:
                    object_classes = [str(RDFS.Resource)]

                for class_uri in class_uris:
                    for object_class_uri in object_classes:
                        stats.increment_resource_property(
                            class_uri, property_uri, object_class_uri
                        )


def collect_dump_stats(
    input_path: str | Path,
    *,
    on_subdataset: Callable[[str], None] | None = None,
    on_progress: Callable[[int, float, float], None] | None = None,
    on_intermediate_result: Callable[[DatasetStats, int], None] | None = None,
    progress_interval_seconds: float = 300.0,
    intermediate_record_interval: int = 1_000_000,
    clock: Callable[[], float] = monotonic,
) -> tuple[DatasetStats, int]:
    """Collect aggregate statistics from every record in an RDF dump."""
    from rdf_dump_reader import RDFDumpReader

    if intermediate_record_interval <= 0:
        raise ValueError("intermediate_record_interval must be greater than zero")

    stats = DatasetStats()
    reader = RDFDumpReader(
        input_path,
        on_parse_error="skip_record",
        invalid_uri_policy="keep",
    )

    processed_records = 0
    current_subdataset: str | None = None
    start_time = clock()
    next_progress_time = start_time + progress_interval_seconds

    for record in reader:
        record_subdataset = getattr(record, "subdataset", None)
        if record_subdataset is not None and record_subdataset != current_subdataset:
            current_subdataset = str(record_subdataset)
            if on_subdataset is not None:
                on_subdataset(current_subdataset)

        collect_graph_stats(record.graph, stats)
        processed_records += 1

        if (
            on_intermediate_result is not None
            and processed_records % intermediate_record_interval == 0
        ):
            on_intermediate_result(stats, processed_records)

        now = clock()
        if on_progress is not None and now >= next_progress_time:
            elapsed_seconds = max(now - start_time, 0.0)
            records_per_second = (
                processed_records / elapsed_seconds if elapsed_seconds > 0 else 0.0
            )
            seconds_per_million = (
                1_000_000 / records_per_second
                if records_per_second > 0
                else float("inf")
            )
            on_progress(processed_records, records_per_second, seconds_per_million)

            if progress_interval_seconds > 0:
                while next_progress_time <= now:
                    next_progress_time += progress_interval_seconds
            else:
                next_progress_time = now

    return stats, processed_records
