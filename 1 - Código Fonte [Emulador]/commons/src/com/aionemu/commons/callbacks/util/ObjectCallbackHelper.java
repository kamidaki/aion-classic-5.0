package com.aionemu.commons.callbacks.util;

import com.aionemu.commons.callbacks.Callback;
import com.aionemu.commons.callbacks.CallbackResult;
import com.aionemu.commons.callbacks.EnhancedObject;
import com.aionemu.commons.callbacks.util.CallbacksUtil;
import com.aionemu.commons.utils.GenericValidator;
import com.google.common.collect.Maps;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ObjectCallbackHelper {
    private static final Logger log = LoggerFactory.getLogger(ObjectCallbackHelper.class);

    private ObjectCallbackHelper() {
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void addCallback(Callback callback, EnhancedObject object) {
        try {
            object.getCallbackLock().writeLock().lock();
            Map<Class<? extends Callback>, List<Callback>> cbMap = object.getCallbacks();
            if (cbMap == null) {
                cbMap = Maps.newHashMap();
                object.setCallbacks(cbMap);
            }
            List<Callback> list = cbMap.get(callback.getBaseClass());
            if (list == null) {
                list = new CopyOnWriteArrayList<Callback>();
                cbMap.put(callback.getBaseClass(), list);
            }
            CallbacksUtil.insertCallbackToList(callback, list);
        }
        finally {
            object.getCallbackLock().writeLock().unlock();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void removeCallback(Callback callback, EnhancedObject object) {
        try {
            object.getCallbackLock().writeLock().lock();
            Map<Class<? extends Callback>, List<Callback>> cbMap = object.getCallbacks();
            if (GenericValidator.isBlankOrNull(cbMap)) {
                return;
            }
            List<Callback> list = cbMap.get(callback.getBaseClass());
            if (list == null || !list.remove(callback)) {
                log.error("Attempt to remove callback that doesn't exists", (Throwable)new RuntimeException());
                return;
            }
            if (list.isEmpty()) {
                cbMap.remove(callback.getBaseClass());
            }
            if (cbMap.isEmpty()) {
                object.setCallbacks(null);
            }
        }
        finally {
            object.getCallbackLock().writeLock().unlock();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static CallbackResult<?> beforeCall(EnhancedObject obj, Class callbackClass, Object ... args) {
        Map<Class<? extends Callback>, List<Callback>> cbMap = obj.getCallbacks();
        if (GenericValidator.isBlankOrNull(cbMap)) {
            return CallbackResult.newContinue();
        }
        CallbackResult cr = null;
        List<Callback> list = null;
        try {
            obj.getCallbackLock().readLock().lock();
            list = cbMap.get(callbackClass);
        }
        finally {
            obj.getCallbackLock().readLock().unlock();
        }
        if (GenericValidator.isBlankOrNull(list)) {
            return CallbackResult.newContinue();
        }
        for (Callback c : list) {
            try {
                cr = c.beforeCall(obj, args);
                if (!cr.isBlockingCallbacks()) continue;
                break;
            }
            catch (Exception e) {
                log.error("Uncaught exception in callback", (Throwable)e);
            }
        }
        return cr == null ? CallbackResult.newContinue() : cr;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static CallbackResult<?> afterCall(EnhancedObject obj, Class callbackClass, Object[] args, Object result) {
        Map<Class<? extends Callback>, List<Callback>> cbMap = obj.getCallbacks();
        if (GenericValidator.isBlankOrNull(cbMap)) {
            return CallbackResult.newContinue();
        }
        CallbackResult cr = null;
        List<Callback> list = null;
        try {
            obj.getCallbackLock().readLock().lock();
            list = cbMap.get(callbackClass);
        }
        finally {
            obj.getCallbackLock().readLock().unlock();
        }
        if (GenericValidator.isBlankOrNull(list)) {
            return CallbackResult.newContinue();
        }
        for (Callback c : list) {
            try {
                cr = c.afterCall(obj, args, result);
                if (!cr.isBlockingCallbacks()) continue;
                break;
            }
            catch (Exception e) {
                log.error("Uncaught exception in callback", (Throwable)e);
            }
        }
        return cr == null ? CallbackResult.newContinue() : cr;
    }
}

