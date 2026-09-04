package com.aionemu.commons.utils.collections;

import java.util.Iterator;
import java.util.NoSuchElementException;

public class IteratorIterator<V>
implements Iterator<V> {
    private Iterator<? extends Iterable<V>> firstLevelIterator;
    private Iterator<V> secondLevelIterator;

    public IteratorIterator(Iterable<? extends Iterable<V>> itit) {
        this.firstLevelIterator = itit.iterator();
    }

    @Override
    public boolean hasNext() {
        if (this.secondLevelIterator != null && this.secondLevelIterator.hasNext()) {
            return true;
        }
        while (this.firstLevelIterator.hasNext()) {
            Iterable<V> iterable = this.firstLevelIterator.next();
            if (iterable == null) continue;
            this.secondLevelIterator = iterable.iterator();
            if (!this.secondLevelIterator.hasNext()) continue;
            return true;
        }
        return false;
    }

    @Override
    public V next() {
        if (this.secondLevelIterator == null || !this.secondLevelIterator.hasNext()) {
            throw new NoSuchElementException();
        }
        return this.secondLevelIterator.next();
    }

    @Override
    public void remove() {
        throw new UnsupportedOperationException("This operation is not supported.");
    }
}

