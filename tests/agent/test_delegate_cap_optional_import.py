"""Non-delegating tools must work without the optional delegation backend."""

import builtins
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from run_agent import AIAgent


def _call(name):
    return SimpleNamespace(function=SimpleNamespace(name=name))


class TestDelegateCapOptionalImport(TestCase):
    def test_zero_delegates_never_import_backend(self):
        original = builtins.__import__

        def guarded(name, *args, **kwargs):
            if name == "tools.delegate_tool":
                raise AssertionError("non-delegating tools imported delegation")
            return original(name, *args, **kwargs)

        with patch("builtins.__import__", guarded):
            for calls in ([], [_call("recall"), _call("search")]):
                self.assertIs(AIAgent._cap_delegate_task_calls(calls), calls)

    def test_delegates_retain_cap_and_other_calls_in_order(self):
        original = builtins.__import__
        backend = SimpleNamespace(_get_max_concurrent_children=lambda: 2)

        def importing(name, *args, **kwargs):
            return backend if name == "tools.delegate_tool" else original(name, *args, **kwargs)

        first, second, excess = _call("delegate_task"), _call("delegate_task"), _call("delegate_task")
        recall = _call("recall")
        with patch("builtins.__import__", importing):
            at_limit = [first, second]
            self.assertIs(AIAgent._cap_delegate_task_calls(at_limit), at_limit)
            result = AIAgent._cap_delegate_task_calls([first, recall, second, excess])
        self.assertEqual(len(result), 3)
        self.assertTrue(all(actual is expected for actual, expected in zip(result, [first, recall, second])))
