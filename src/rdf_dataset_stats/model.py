"""Internal statistics data model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator


@dataclass
class ResourceObjectClassCounts:
    """Counts of resource object values grouped by object class URI."""

    counts: dict[str, int] = field(default_factory=dict)

    def __getitem__(self, object_class_uri: str) -> int:
        return self.counts[object_class_uri]

    def __contains__(self, object_class_uri: object) -> bool:
        return object_class_uri in self.counts

    def __iter__(self) -> Iterator[str]:
        return iter(self.counts)

    def __len__(self) -> int:
        return len(self.counts)

    def increment(self, object_class_uri: str, amount: int = 1) -> None:
        self.counts[object_class_uri] = self.counts.get(object_class_uri, 0) + amount

    def sorted_items(self) -> list[tuple[str, int]]:
        return sorted(self.counts.items())


@dataclass
class PropertyStats:
    """Aggregated counts for one property under one subject class."""

    literal_count: int = 0
    resource_counts: ResourceObjectClassCounts = field(
        default_factory=ResourceObjectClassCounts
    )

    def increment_literal(self, amount: int = 1) -> None:
        self.literal_count += amount

    def increment_resource(self, object_class_uri: str, amount: int = 1) -> None:
        self.resource_counts.increment(object_class_uri, amount)


@dataclass
class ClassStats:
    """Aggregated counts for one RDF subject class."""

    class_count: int = 0
    properties: dict[str, PropertyStats] = field(default_factory=dict)

    def increment_class(self, amount: int = 1) -> None:
        self.class_count += amount

    def property_stats(self, property_uri: str) -> PropertyStats:
        return self.properties.setdefault(property_uri, PropertyStats())

    def increment_literal_property(self, property_uri: str, amount: int = 1) -> None:
        self.property_stats(property_uri).increment_literal(amount)

    def increment_resource_property(
        self, property_uri: str, object_class_uri: str, amount: int = 1
    ) -> None:
        self.property_stats(property_uri).increment_resource(object_class_uri, amount)

    def sorted_properties(self) -> list[tuple[str, PropertyStats]]:
        return sorted(self.properties.items())


@dataclass
class DatasetStats:
    """Aggregated statistics for a full RDF dataset."""

    classes: dict[str, ClassStats] = field(default_factory=dict)

    def __getitem__(self, class_uri: str) -> ClassStats:
        return self.classes.setdefault(class_uri, ClassStats())

    def __contains__(self, class_uri: object) -> bool:
        return class_uri in self.classes

    def __iter__(self) -> Iterator[str]:
        return iter(self.classes)

    def __len__(self) -> int:
        return len(self.classes)

    def increment_class(self, class_uri: str, amount: int = 1) -> None:
        self[class_uri].increment_class(amount)

    def increment_literal_property(
        self, class_uri: str, property_uri: str, amount: int = 1
    ) -> None:
        self[class_uri].increment_literal_property(property_uri, amount)

    def increment_resource_property(
        self, class_uri: str, property_uri: str, object_class_uri: str, amount: int = 1
    ) -> None:
        self[class_uri].increment_resource_property(
            property_uri, object_class_uri, amount
        )

    def sorted_classes(self) -> list[tuple[str, ClassStats]]:
        return sorted(self.classes.items())
