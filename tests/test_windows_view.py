from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from vibebar_windows.language import LanguageController
from vibebar_windows.break_view import CombinedMenuViewSocket
from vibebar_windows.view_model import ActivityItem, VibeBarView, parse_swiftbar_output


ROOT = Path(__file__).resolve().parents[1]


class LegacyViewTests(unittest.TestCase):
    def test_named_sections_do_not_depend_on_tab_order(self) -> None:
        output = """▶ task
---
BREAKS | vibebar_section=breaks
09:00  pause
---
TASKS | vibebar_section=tasks
09:10  actual task
---
IDEAS | vibebar_section=ideas
09:20  an idea
---
TODOS | vibebar_section=todos
09:30  a todo
---
CLIPBOARD | vibebar_section=clipboard
capture
"""
        view = parse_swiftbar_output(output)
        self.assertEqual(view.tasks[0].text, "actual task")
        self.assertEqual(view.ideas[0].text, "an idea")
        self.assertEqual(view.todos[0].text, "a todo")

    def test_original_swiftbar_sections_become_typed_view(self) -> None:
        output = """▸ current task · 4m
---
TASKS (1) | color=x
12:00  first task | color=x
---
IDEAS (1) | color=x
12:01  useful idea | color=x
---
TODOS (1) | color=x
12:02  call later | color=x
---
CLIPBOARD (1) | color=x
capture | action=x
1  copied text | param2=7 color=x
👁 show | color=x
---
actions
"""
        view = parse_swiftbar_output(output)
        self.assertEqual(view.current, "current task · 4m")
        self.assertEqual(view.tasks[0].text, "first task")
        self.assertEqual(view.ideas[0].text, "useful idea")
        self.assertEqual(view.todos[0].text, "call later")
        self.assertEqual(view.clipboard[0].source_index, 7)

    def test_breaks_are_also_visible_in_main_timeline(self) -> None:
        inner = StaticView(VibeBarView("current", (ActivityItem("16:05", "work"),), (), (), ()))
        breaks = StaticBreaks((ActivityItem("15:47", "⏸ break"),))
        view = CombinedMenuViewSocket(inner, breaks).load()
        self.assertEqual([item.time for item in view.tasks], ["16:05", "15:47"])
        self.assertEqual(view.breaks[0].time, "15:47")


class StaticView:
    def __init__(self, view: VibeBarView) -> None:
        self.view = view

    def load(self) -> VibeBarView:
        return self.view


class StaticBreaks:
    def __init__(self, items: tuple[ActivityItem, ...]) -> None:
        self.items = items

    def load(self) -> tuple[ActivityItem, ...]:
        return self.items


class LanguageTests(unittest.TestCase):
    def test_language_switch_is_persisted_and_replaceable(self) -> None:
        locale_dir = ROOT / "resources" / "locales"
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            settings = Path(directory) / "settings.json"
            controller = LanguageController(locale_dir, settings)
            self.assertEqual(controller.catalog.code, "he")
            self.assertEqual(controller.switch().code, "ru")
            self.assertEqual(json.loads(settings.read_text(encoding="utf-8"))["language"], "ru")

    def test_every_locale_has_the_same_contract(self) -> None:
        locale_dir = ROOT / "resources" / "locales"
        catalogs = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(locale_dir.glob("*.json"))]
        expected = set(catalogs[0])
        self.assertTrue(all(set(catalog) == expected for catalog in catalogs[1:]))


if __name__ == "__main__":
    unittest.main()
