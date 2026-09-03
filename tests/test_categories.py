from datetime import datetime
from pathlib import Path
import tempfile
import unittest

from vibebar_modular.categories import Category, CategoryService, JsonClassificationRepository, NullClassificationRepository
from vibebar_modular.category_reports import MarkdownCategoryReportWriter, NullCategoryReportWriter


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 9, 1, 15, 0)


class CategoryTests(unittest.TestCase):
    def test_assignment_aggregates_different_transcriptions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            journal = root / "journal.md"
            journal.write_text(
                "## 2026-09-01\n- 14:00 · לכתוב\n- 14:20 · לחתור\n- 14:40 · ⏸ הפסקה\n",
                encoding="utf-8",
            )
            store = JsonClassificationRepository(root / "classes.json")
            service = CategoryService(journal, (Category(1, {"he": "כתיבה", "ru": "Письмо", "en": "Writing"}),), store, FixedClock())
            tasks = service.tasks()
            service.assign(tasks[0].key, 1)
            service.assign(tasks[1].key, 1)
            self.assertIn("0h 40m", service.summary(1, "he"))

    def test_report_marker_updates_without_touching_manual_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            report = root / "report.md"
            report.write_text("manual note\n", encoding="utf-8")
            writer = MarkdownCategoryReportWriter()
            writer.enrich(report, "summary")
            writer.enrich(report, "summary")
            content = report.read_text(encoding="utf-8")
            self.assertIn("manual note", content)
            self.assertEqual(content.count(writer.MARK_START), 1)

    def test_null_report_writer_is_sealed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.md"
            NullCategoryReportWriter().enrich(report, "summary")
            self.assertFalse(report.exists())


if __name__ == "__main__":
    unittest.main()
