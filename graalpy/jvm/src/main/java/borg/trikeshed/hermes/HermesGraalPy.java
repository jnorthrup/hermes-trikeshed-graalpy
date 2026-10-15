/* Copyright (c) Glamdring Incorporated. SPDX-License-Identifier: AGPL-3.0-only */
package borg.trikeshed.hermes;

import java.io.File;
import java.nio.file.Path;
import java.security.Security;
import org.graalvm.polyglot.Context;
import org.graalvm.polyglot.EnvironmentAccess;
import org.graalvm.polyglot.HostAccess;
import org.graalvm.polyglot.PolyglotAccess;
import org.graalvm.polyglot.PolyglotException;
import org.graalvm.polyglot.Source;
import org.graalvm.polyglot.io.IOAccess;

/** One stock GraalPy context for the original CLI on this process's normal terminal. */
public final class HermesGraalPy {
    public static void main(String[] args) throws Exception {
        if (args.length == 0) throw new IllegalArgumentException("usage: HermesGraalPy <venv/bin/python> [Hermes CLI arguments]");
        Path root = Path.of(System.getProperty("hermes.root", ".")).toAbsolutePath().normalize();
        Path executable = Path.of(args[0]).toAbsolutePath().normalize();
        String[] pythonArgs = new String[args.length];
        pythonArgs[0] = root.resolve("cli.py").toString();
        System.arraycopy(args, 1, pythonArgs, 1, args.length - 1);
        Security.addProvider(new PythonBlake2Provider());
        try (Context context = Context.newBuilder("python")
                .allowExperimentalOptions(true)
                .allowHostAccess(HostAccess.NONE).allowHostClassLookup(name -> false)
                .allowPolyglotAccess(PolyglotAccess.NONE).allowIO(IOAccess.ALL)
                .allowNativeAccess(true).allowCreateThread(true).allowCreateProcess(true)
                .allowEnvironmentAccess(EnvironmentAccess.INHERIT)
                .option("engine.WarnInterpreterOnly", "false")
                .option("python.PosixModuleBackend", "native")
                .option("python.TerminalIsInteractive", Boolean.toString(System.console() != null))
                .option("python.AllowSignalHandlers", "true")
                .option("python.InstallSignalHandlers", "true")
                .option("python.ForceImportSite", "true")
                .option("python.Executable", executable.toString())
                .option("python.PythonPath", root + File.pathSeparator + root.resolve("graalpy/bridges"))
                .arguments("python", pythonArgs)
                .in(System.in).out(System.out).err(System.err).build()) {
            context.eval(Source.newBuilder("python", root.resolve("graalpy/cli.py").toFile()).name("graalpy/cli.py").build());
        } catch (PolyglotException error) {
            if (error.isExit()) System.exit(error.getExitStatus());
            throw error;
        }
    }
}
