"""Run the original Hermes CLI with the two required Python compatibility bridges."""

import trikeshed_contextvars

trikeshed_contextvars.install()

import cli
import fire
import threading
import traceback
import trikeshed_posix

trikeshed_posix.install()
try:
    fire.Fire(cli.main)
except Exception:
    traceback.print_exc()
    raise
finally:
    # The stock CLI marks its bound-method workers for exit during shutdown.
    # Await their actual native SQLite work before retiring the only context.
    workers = [thread for thread in threading.enumerate()
               if thread is not threading.current_thread()
               and isinstance(getattr(getattr(thread, "_target", None), "__self__", None), cli.HermesCLI)]
    for thread in workers:
        thread.join()
    from hermes_state_registry import close_all
    close_all()
