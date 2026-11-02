"""Host tool declarations affect execution placement, never tool arguments or policy."""

from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from agent.host_tool_transport import host_tool_deadline
from agent import tool_executor
from tools.registry import registry


class TestHostToolTransport(TestCase):
    def test_declaration_requires_registered_handler_and_finite_deadline(self):
        handler = lambda arguments: arguments
        with patch.object(registry, "get_entry", return_value=None):
            self.assertIsNone(host_tool_deadline("missing"))
        with patch.object(registry, "get_entry", return_value=SimpleNamespace(handler=handler)):
            self.assertIsNone(host_tool_deadline("host"))
            for invalid in (True, 0, -1, float("inf"), float("nan"), 301, "30"):
                handler.HERMES_HOST_TIMEOUT_SECONDS = invalid
                with self.assertRaises(ValueError):
                    host_tool_deadline("host")
            handler.HERMES_HOST_TIMEOUT_SECONDS = 30.0
            self.assertEqual(host_tool_deadline("host"), 30.0)

    def test_host_call_retains_middleware_without_guest_worker_or_heartbeat(self):
        handler = lambda arguments: arguments
        handler.HERMES_HOST_TIMEOUT_SECONDS = 30.0
        entry = SimpleNamespace(handler=handler)
        marker = object()
        with (patch.object(registry, "get_entry", return_value=entry),
              patch.object(tool_executor, "_run_agent_tool_execution_middleware", return_value=marker) as middleware,
              patch.object(tool_executor.threading.Thread, "start", side_effect=AssertionError("guest thread"))):
            result = tool_executor._run_sequential_tool_execution_middleware(
                object(), function_name="recall", function_args={"HERMES_HOST_TIMEOUT_SECONDS": 1},
                effective_task_id="task", tool_call_id="call", execute=handler)
            self.assertIs(result, marker)
            middleware.assert_called_once()
            self.assertIs(tool_executor._run_with_activity_heartbeat(object(), "recall", lambda: marker), marker)

    def test_tool_arguments_do_not_mark_an_unmarked_handler(self):
        entry = SimpleNamespace(handler=lambda arguments: arguments)
        with (patch.object(registry, "get_entry", return_value=entry),
              patch("tools.daemon_pool.DaemonThreadPoolExecutor", side_effect=RuntimeError("ordinary worker retained"))):
            with self.assertRaisesRegex(RuntimeError, "ordinary worker retained"):
                tool_executor._run_sequential_tool_execution_middleware(
                    object(), function_name="recall", function_args={"HERMES_HOST_TIMEOUT_SECONDS": 30},
                    effective_task_id="task", tool_call_id="call", execute=entry.handler)
