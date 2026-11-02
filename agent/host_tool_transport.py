"""Host-owned tools retain registry and policy dispatch while their host owns the deadline."""

import math


def host_tool_deadline(function_name):
    from tools.registry import registry

    entry = registry.get_entry(function_name)
    seconds = getattr(entry.handler, "HERMES_HOST_TIMEOUT_SECONDS", None) if entry is not None else None
    if seconds is None:
        return None
    if (isinstance(seconds, bool) or not isinstance(seconds, (int, float))
            or not math.isfinite(seconds) or not 0 < seconds <= 300):
        raise ValueError("Host tool requires a positive finite deadline within 300 seconds")
    return seconds
