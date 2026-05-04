from rdf_dataset_stats.model import DatasetStats


def test_create_empty_statistics() -> None:
    stats = DatasetStats()

    assert len(stats) == 0
    assert stats.classes == {}


def test_increment_class_counts() -> None:
    stats = DatasetStats()

    stats.increment_class("http://example.org/Class")
    stats.increment_class("http://example.org/Class", amount=2)

    assert stats["http://example.org/Class"].class_count == 3


def test_increment_literal_property_counts() -> None:
    stats = DatasetStats()

    stats.increment_literal_property(
        "http://example.org/Class", "http://example.org/title"
    )
    stats.increment_literal_property(
        "http://example.org/Class", "http://example.org/title", amount=4
    )

    property_stats = stats["http://example.org/Class"].properties[
        "http://example.org/title"
    ]
    assert property_stats.literal_count == 5


def test_increment_resource_object_class_counts() -> None:
    stats = DatasetStats()

    stats.increment_resource_property(
        "http://example.org/Class",
        "http://example.org/related",
        "http://example.org/ObjectClass",
    )
    stats.increment_resource_property(
        "http://example.org/Class",
        "http://example.org/related",
        "http://example.org/ObjectClass",
        amount=2,
    )

    property_stats = stats["http://example.org/Class"].properties[
        "http://example.org/related"
    ]
    assert property_stats.resource_counts["http://example.org/ObjectClass"] == 3


def test_sorted_access_is_deterministic() -> None:
    stats = DatasetStats()
    stats.increment_class("http://example.org/Z")
    stats.increment_class("http://example.org/A")
    stats.increment_literal_property("http://example.org/Z", "http://example.org/b")
    stats.increment_literal_property("http://example.org/Z", "http://example.org/a")
    stats.increment_resource_property(
        "http://example.org/Z",
        "http://example.org/b",
        "http://example.org/ObjectZ",
    )
    stats.increment_resource_property(
        "http://example.org/Z",
        "http://example.org/b",
        "http://example.org/ObjectA",
    )

    assert [class_uri for class_uri, _ in stats.sorted_classes()] == [
        "http://example.org/A",
        "http://example.org/Z",
    ]
    assert [property_uri for property_uri, _ in stats["http://example.org/Z"].sorted_properties()] == [
        "http://example.org/a",
        "http://example.org/b",
    ]
    resource_counts = stats["http://example.org/Z"].properties[
        "http://example.org/b"
    ].resource_counts
    assert resource_counts.sorted_items() == [
        ("http://example.org/ObjectA", 1),
        ("http://example.org/ObjectZ", 1),
    ]
