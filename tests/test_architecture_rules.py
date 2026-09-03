from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CODE_ROOTS = (
    ROOT / "vibebar_modular",
    ROOT / "vibebar_windows",
    ROOT / "vibebar_macos",
    ROOT / "vibebar_voice",
    ROOT / "windows" / "helpers",
    ROOT / "blocks" / "absence_break",
    ROOT / "blocks" / "bluetooth_proximity",
    ROOT / "tests",
)


class ArchitectureRulesTests(unittest.TestCase):
    def source_files(self) -> list[Path]:
        """Return every Python file maintained by this fork, at any depth."""
        return sorted({
            path
            for root in CODE_ROOTS
            for path in root.rglob("*.py")
            if not any(part.startswith(".") or part == "__pycache__" for part in path.relative_to(ROOT).parts)
        })

    def test_files_do_not_exceed_400_lines(self) -> None:
        oversized = [path.name for path in self.source_files() if len(path.read_text(encoding="utf-8").splitlines()) > 400]
        self.assertEqual(oversized, [])

    def test_production_modules_explain_their_responsibility(self) -> None:
        """A module boundary must say why it exists, not rely on its filename."""
        production = [path for path in self.source_files() if "tests" not in path.parts and path.name != "__init__.py"]
        missing = [str(path.relative_to(ROOT)) for path in production if ast.get_docstring(
            ast.parse(path.read_text(encoding="utf-8"))
        ) is None]
        self.assertEqual(missing, [])

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
            if path.name == "clock.py":
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "now"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "datetime"
                ):
                    violations.append(f"{path.name}:{node.lineno}")
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

    def test_platform_adapters_do_not_import_each_other(self) -> None:
        mac = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "vibebar_macos").glob("*.py"))
        windows = "\n".join(path.read_text(encoding="utf-8") for path in (ROOT / "vibebar_windows").glob("*.py"))
        self.assertNotIn("vibebar_windows", mac)
        self.assertNotIn("vibebar_macos", windows)

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
