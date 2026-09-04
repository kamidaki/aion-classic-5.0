package com.aionemu.commons.callbacks;

import com.aionemu.commons.callbacks.CallbackResult;

public interface Callback<T> {
    public CallbackResult beforeCall(T var1, Object[] var2);

    public CallbackResult afterCall(T var1, Object[] var2, Object var3);

    public Class<? extends Callback> getBaseClass();
}

