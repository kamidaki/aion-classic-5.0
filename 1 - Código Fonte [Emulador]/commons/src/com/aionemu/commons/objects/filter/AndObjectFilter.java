package com.aionemu.commons.objects.filter;

import com.aionemu.commons.objects.filter.ObjectFilter;

public class AndObjectFilter<T>
implements ObjectFilter<T> {
    private ObjectFilter<? super T>[] filters;

    public AndObjectFilter(ObjectFilter<? super T> ... filters) {
        this.filters = filters;
    }

    @Override
    public boolean acceptObject(T object) {
        for (ObjectFilter<? super T> objectFilter : this.filters) {
            if (objectFilter == null || objectFilter.acceptObject(object)) continue;
            return false;
        }
        return true;
    }
}

