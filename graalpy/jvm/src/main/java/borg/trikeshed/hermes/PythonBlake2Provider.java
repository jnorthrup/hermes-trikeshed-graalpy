/* Copyright (c) Glamdring Incorporated. SPDX-License-Identifier: AGPL-3.0-only */
package borg.trikeshed.hermes;

import java.security.MessageDigestSpi;
import java.security.Provider;
import java.util.List;
import java.util.Map;
import org.bouncycastle.crypto.digests.Blake2bDigest;

/** Java equivalent of the hosted provider: GraalPy 25.3 names byte counts as JCA bit counts. */
public final class PythonBlake2Provider extends Provider {
    public PythonBlake2Provider() {
        super("TrikeShedGraalPyBlake2", "1.0", "GraalPy BLAKE2b byte-length bridge");
        for (int bytes = 1; bytes <= 64; bytes++) {
            final int size = bytes;
            putService(new Service(this, "MessageDigest", "BLAKE2B-" + bytes,
                    Digest.class.getName(), List.of(), Map.of()) {
                @Override public Object newInstance(Object parameter) {
                    if (parameter != null) throw new IllegalArgumentException("unexpected digest parameter");
                    return new Digest(size);
                }
            });
        }
    }

    public static final class Digest extends MessageDigestSpi implements Cloneable {
        private Blake2bDigest digest;
        public Digest(int bytes) { digest = new Blake2bDigest(bytes * 8); }
        @Override protected int engineGetDigestLength() { return digest.getDigestSize(); }
        @Override protected void engineUpdate(byte input) { digest.update(input); }
        @Override protected void engineUpdate(byte[] input, int offset, int length) { digest.update(input, offset, length); }
        @Override protected byte[] engineDigest() {
            byte[] output = new byte[digest.getDigestSize()];
            digest.doFinal(output, 0);
            return output;
        }
        @Override protected void engineReset() { digest.reset(); }
        @Override public Object clone() throws CloneNotSupportedException {
            Digest copy = (Digest) super.clone();
            copy.digest = new Blake2bDigest(digest);
            return copy;
        }
    }
}
