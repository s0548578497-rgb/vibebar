import unittest

from vibebar_windows.hotkey import NullGlobalHotkey


class HotkeyBoundaryTests(unittest.TestCase):
    def test_null_hotkey_is_sealed(self) -> None:
        hotkey = NullGlobalHotkey()
        hotkey.start()
        hotkey.close()


if __name__ == "__main__":
    unittest.main()
