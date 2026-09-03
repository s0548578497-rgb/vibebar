"""Compatibility imports for shared task categories."""

from vibebar_modular.categories import (
    Category, CategoryService, ClassificationRepository, JsonClassificationRepository,
    NullClassificationRepository, TimedTask, load_categories,
)

__all__ = [
    "Category", "CategoryService", "ClassificationRepository", "JsonClassificationRepository",
    "NullClassificationRepository", "TimedTask", "load_categories",
]
