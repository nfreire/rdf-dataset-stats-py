from rdflib import BNode, Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS

from rdf_dataset_stats.collector import collect_graph_stats
from rdf_dataset_stats.model import DatasetStats


EX = "http://example.org/"


def uri(name: str) -> URIRef:
    return URIRef(f"{EX}{name}")


def collect(graph: Graph) -> DatasetStats:
    stats = DatasetStats()
    collect_graph_stats(graph, stats)
    return stats


def test_counts_class_usage() -> None:
    graph = Graph()
    graph.add((uri("subject"), RDF.type, uri("Class")))

    stats = collect(graph)

    assert stats[str(uri("Class"))].class_count == 1


def test_counts_literal_property_usage_for_typed_subject() -> None:
    graph = Graph()
    graph.add((uri("subject"), RDF.type, uri("Class")))
    graph.add((uri("subject"), uri("title"), Literal("Title")))

    stats = collect(graph)

    property_stats = stats[str(uri("Class"))].properties[str(uri("title"))]
    assert property_stats.literal_count == 1


def test_counts_resource_property_usage_with_typed_object() -> None:
    graph = Graph()
    graph.add((uri("subject"), RDF.type, uri("Class")))
    graph.add((uri("subject"), uri("related"), uri("object")))
    graph.add((uri("object"), RDF.type, uri("ObjectClass")))

    stats = collect(graph)

    resource_counts = stats[str(uri("Class"))].properties[
        str(uri("related"))
    ].resource_counts
    assert resource_counts[str(uri("ObjectClass"))] == 1


def test_counts_untyped_resource_object_as_rdfs_resource() -> None:
    graph = Graph()
    graph.add((uri("subject"), RDF.type, uri("Class")))
    graph.add((uri("subject"), uri("related"), uri("object")))

    stats = collect(graph)

    resource_counts = stats[str(uri("Class"))].properties[
        str(uri("related"))
    ].resource_counts
    assert resource_counts[str(RDFS.Resource)] == 1


def test_counts_object_with_multiple_types_once_per_object_type() -> None:
    graph = Graph()
    graph.add((uri("subject"), RDF.type, uri("Class")))
    graph.add((uri("subject"), uri("related"), uri("object")))
    graph.add((uri("object"), RDF.type, uri("ObjectClassA")))
    graph.add((uri("object"), RDF.type, uri("ObjectClassB")))

    stats = collect(graph)

    resource_counts = stats[str(uri("Class"))].properties[
        str(uri("related"))
    ].resource_counts
    assert resource_counts[str(uri("ObjectClassA"))] == 1
    assert resource_counts[str(uri("ObjectClassB"))] == 1


def test_counts_subject_property_under_each_subject_type() -> None:
    graph = Graph()
    graph.add((uri("subject"), RDF.type, uri("ClassA")))
    graph.add((uri("subject"), RDF.type, uri("ClassB")))
    graph.add((uri("subject"), uri("title"), Literal("Title")))

    stats = collect(graph)

    assert (
        stats[str(uri("ClassA"))].properties[str(uri("title"))].literal_count == 1
    )
    assert (
        stats[str(uri("ClassB"))].properties[str(uri("title"))].literal_count == 1
    )


def test_ignores_properties_of_untyped_subjects() -> None:
    graph = Graph()
    graph.add((uri("subject"), uri("title"), Literal("Title")))

    stats = collect(graph)

    assert len(stats) == 0


def test_excludes_rdf_type_from_property_statistics() -> None:
    graph = Graph()
    graph.add((uri("subject"), RDF.type, uri("Class")))

    stats = collect(graph)

    assert stats[str(uri("Class"))].properties == {}


def test_counts_bnode_resource_objects() -> None:
    graph = Graph()
    object_node = BNode()
    graph.add((uri("subject"), RDF.type, uri("Class")))
    graph.add((uri("subject"), uri("related"), object_node))
    graph.add((object_node, RDF.type, uri("ObjectClass")))

    stats = collect(graph)

    resource_counts = stats[str(uri("Class"))].properties[
        str(uri("related"))
    ].resource_counts
    assert resource_counts[str(uri("ObjectClass"))] == 1
