package com.aionemu.commons.utils;

import java.util.Collection;
import java.util.LinkedHashSet;

/**
 * High performance ordered set compatible with FIFO periodic queues.
 * Modernized for Java 25 using SequencedSet (LinkedHashSet).
 *
 * @param <E> element type
 */
public class AEFastSet<E> extends LinkedHashSet<E> {
    private static final long serialVersionUID = 1L;

    public AEFastSet() {
        super();
    }

    public AEFastSet(int capacity) {
        super(capacity);
    }

    public AEFastSet(Collection<? extends E> c) {
        super(c);
    }

    @Override
    public E removeFirst() {
        if (isEmpty()) {
            return null;
        }
        return super.removeFirst();
    }
}
