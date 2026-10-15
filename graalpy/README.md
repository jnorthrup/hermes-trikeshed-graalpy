# Hermes on stock GraalPy

This directory contains the TrikeShed port additions. The upstream Hermes source
outside this directory is retained at the revision recorded in `provenance.json`.
Hermes runs its original CLI, agent loop, tools, OpenAI SDK, and SQLite session
store. The standalone entry uses one stock GraalPy context in one JVM process.

The standalone terminal was verified with typed `/help`, a real NVIDIA Nemotron
Ultra 550 turn calling `read_file` on `LICENSE`, the final model reply, native
SQLite persistence, and `/quit` returning exit code 0. The sanitized evidence is
in [`verification/standalone-agent-turn.json`](verification/standalone-agent-turn.json).

## Build and run in a normal terminal

The verified runtime is GraalPy Community 25.3.4.1, Python 3.13.14, with GraalVM
Community JDK 25.0.4.1 on macOS ARM64. A 64-bit Linux native POSIX installation
is supported by the positional-read bridge but has not been verified here.
Windows is not supported by this bridge.

Install the matching GraalPy distribution and JDK, then run from the repository root:

```sh
graalpy -m venv .venv-graalpy
.venv-graalpy/bin/python -m pip install -r graalpy/requirements.txt
mvn -f graalpy/jvm/pom.xml package dependency:copy-dependencies -DincludeScope=runtime
java --enable-native-access=ALL-UNNAMED -Xmx2g \
  -cp 'graalpy/jvm/target/classes:graalpy/jvm/target/dependency/*' \
  borg.trikeshed.hermes.HermesGraalPy .venv-graalpy/bin/python
```

Pass normal `cli.py` arguments after the interpreter path, for example `--help`,
`--resume SESSION_ID`, or `--toolsets terminal,file`. This invokes the original
`cli.main` and its interactive TUI on the terminal's actual input/output. It does
not start the Hermes gateway or TrikeShed server. Run each concurrent CLI in a
separate JVM process; do not create another native Python context in that process.

`requirements.txt` is the exact installed-package freeze from the working port.
It is a snapshot of the CLI core, not upstream Hermes' full optional dependency
set. Native packages may require a C/Rust toolchain to build for GraalPy.
Optional integrations remain subject to their real dependencies and are not
replaced with stubs.

## Provider configuration

Use stock Hermes configuration and credentials. A separate `HERMES_HOME`
keeps port sessions and configuration separate from another Hermes installation.
The verified provider configuration is:

```yaml
model:
  provider: nvidia
  default: nvidia/nemotron-3-ultra-550b-a55b
  base_url: https://integrate.api.nvidia.com/v1
  key_env: NVIDIA_API_KEY
```

Supply `NVIDIA_API_KEY` through the environment or the private `.env` belonging to
that Hermes home. No credentials, profiles, sessions, databases, or cache files
are included in this port.

`config.example.yaml` contains this configuration and disables automatic title
model upgrades, keeping auxiliary model selection from drifting to another
model. Copy it to the separate Hermes home's `config.yaml`, and export your
existing `NVIDIA_API_KEY` in your terminal before launch. The stock NVIDIA
resolver reads this provider-specific key; a generic `model.api_key` is not a
substitute.

## Compatibility boundaries

`bridges/trikeshed_contextvars.py` retains the actual names declared by
`gateway.session_context` when GraalPy lacks `ContextVar.name`. It validates that
source's AST and fails when the expected shape changes. It does not replace
`contextvars` or alter the upstream file.

`bridges/trikeshed_posix.py` supplies a genuine libc `pread` only to
`hermes_state_dbfile` when native GraalPy lacks `os.pread`. File descriptor
ownership remains with Hermes. It requires GraalPy's native POSIX backend.

`jvm/PythonBlake2Provider.kt` is the original hosted JCA provider. The Java
equivalent in `jvm/src/main/java` makes the same byte-to-bit correction using
Bouncy Castle's actual BLAKE2b implementation. GraalPy 25.3 requests names such as
`BLAKE2B-16` for a 16-byte digest; the stock provider exposes bit-length names.
Registering the provider before creating the context resolves this mismatch.
Running this runtime's native `python cli.py` directly bypasses that registration
and is not an equivalent supported invocation.

The Java entry enables native POSIX I/O, native extensions, threads, processes,
environment access, and stock Python signal handlers for this CLI. The latter
are disabled by default when embedding; prompt_toolkit's main-thread input loop
requires them. The entry also passes the actual console's interactive status
and awaits the original CLI workers before closing its session registry and
context. Python has no Java class access. Actual
Python `open`, `subprocess`, HTTPX, and OpenAI remain the stock implementations.

## TrikeShed hosting

The four files under `bridges/` are copied verbatim from the working TrikeShed
port. The standalone CLI imports only the two compatibility adapters above.

`trikeshed_cli_worker.py` hosts the actual `HermesCLI.run()` loop with native
terminal transport, admission/completion receipts, resize, session resume, and
awaited shutdown. Its `start(host_call, ...)` API requires the real TrikeShed host
crossing. `trikeshed_modelmux.py` registers the optional `trikeshed` provider;
other providers still use the genuine Hermes SDK path. Its SSE adapter buffers a
completed response and does not claim network streaming.

Host-owned ModelMux delegates are `mux_catalog` and `mux_completion`; progress
uses `sleeve_progress`, and CLI exit reports through `sleeve_cli_closed`.
The hosted bootstrap binds the real delegates before
starting the worker. A no-op callback is not an implementation of that contract.
The standalone CLI does not register this provider or emulate these delegates.

## License

The original Hermes source remains under its upstream MIT license. The additions
in `graalpy/` are copied or derived from TrikeShed, copyright Glamdring
Incorporated, under AGPLv3; see `LICENSE` and `NOTICE.md` in this directory.
Runtime and dependency artifacts retain their own licenses and are not vendored.
