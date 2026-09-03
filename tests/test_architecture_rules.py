from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PACKAGES = (
    ROOT / "vibebar_modular",
    ROOT / "vibebar_windows",
    ROOT / "vibebar_macos",
    ROOT / "windows" / "helpers",
)


class ArchitectureRulesTests(unittest.TestCase):
    def source_files(self) -> list[Path]:
        return sorted(path for package in PACKAGES for path in package.glob("*.py"))

    def test_files_do_not_exceed_400_lines(self) -> None:
        oversized = [path.name for path in self.source_files() if len(path.read_text(encoding="utf-8").splitlines()) > 400]
        self.assertEqual(oversized, [])

    def test_functions_do_not_exceed_50_lines(self) -> None:
        oversized: list[str] = []
        for path in self.source_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    length = (node.end_lineno or node.lineno) - node.lineno + 1
                    if length > 50:
                        oversized.append(f"{path.name}:{node.name}")
        self.assertEqual(oversized, [])

    def test_no_print_calls(self) -> None:
        self.assertEqual(self._calls_named("print"), [])

    def test_datetime_now_is_isolated_to_clock(self) -> None:
        violations: list[str] = []
        for path in self.source_files():
            if path.name != "clock.py" and "datetime.now(" in path.read_text(encoding="utf-8"):
                violations.append(path.name)
        self.assertEqual(violations, [])

    def test_no_bare_exception_handler(self) -> None:
        violations: list[str] = []
        for path in self.source_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    violations.append(f"{path.name}:{node.lineno}")
        self.assertEqual(violations, [])

    def test_ui_does_not_select_command_implementations(self) -> None:
        source = (ROOT / "vibebar_windows" / "app.py").read_text(encoding="utf-8")
        self.assertNotIn("CustomCommandStore", source)
        self.assertNotIn("LocalizedEntrySocket", source)
        self.assertNotIn("CommandVocabulary", source)
        self.assertNotIn("CppTurboTranscriber", source)
        self.assertNotIn("LegacyMenuViewSocket", source)
        self.assertNotIn("WindowsBashRunner", source)

    def test_ui_does_not_poll_business_data(self) -> None:
        source = (ROOT / "vibebar_windows" / "app.py").read_text(encoding="utf-8")
        self.assertNotIn("after(3000", source)
        self.assertNotIn("_refresh_tick", source)

    def _calls_named(self, name: str) -> list[str]:
        violations: list[str] = []
        for path in self.source_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == name:
                    violations.append(f"{path.name}:{node.lineno}")
        return violations


if __name__ == "__main__":
    unittest.main()
