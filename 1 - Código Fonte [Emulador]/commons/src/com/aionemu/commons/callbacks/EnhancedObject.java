package com.aionemu.commons.callbacks;

import com.aionemu.commons.callbacks.Callback;
import java.util.List;
import java.util.Map;
import java.util.concurrent.locks.ReentrantReadWriteLock;

public interface EnhancedObject {
    public void addCallback(Callback var1);

    public void removeCallback(Callback var1);

    public Map<Class<? extends Callback>, List<Callback>> getCallbacks();

    public void setCallbacks(Map<Class<? extends Callback>, List<Callback>> var1);

    public ReentrantReadWriteLock getCallbackLock();
}

