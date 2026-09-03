import unittest

from absence_break.single_instance import NullInstanceGuard


class SingleInstanceTests(unittest.TestCase):
    def test_null_guard_is_safe_and_repeatable(self) -> None:
        guard = NullInstanceGuard()
        self.assertTrue(guard.acquire())
        guard.close()
