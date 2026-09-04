package com.aionemu.commons.callbacks.util;

import com.aionemu.commons.callbacks.Callback;
import com.aionemu.commons.callbacks.CallbackResult;
import com.aionemu.commons.callbacks.util.CallbacksUtil;
import com.aionemu.commons.utils.ClassUtils;
import java.util.concurrent.CopyOnWriteArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class GlobalCallbackHelper {
    private static final Logger log = LoggerFactory.getLogger(GlobalCallbackHelper.class);
    private static final CopyOnWriteArrayList<Callback> globalCallbacks = new CopyOnWriteArrayList();

    private GlobalCallbackHelper() {
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void addCallback(Callback<?> callback) {
        Class<GlobalCallbackHelper> clazz = GlobalCallbackHelper.class;
        synchronized (GlobalCallbackHelper.class) {
            CallbacksUtil.insertCallbackToList(callback, globalCallbacks);
            // ** MonitorExit[var1_1] (shouldn't be in output)
            return;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void removeCallback(Callback<?> callback) {
        Class<GlobalCallbackHelper> clazz = GlobalCallbackHelper.class;
        synchronized (GlobalCallbackHelper.class) {
            globalCallbacks.remove(callback);
            // ** MonitorExit[var1_1] (shouldn't be in output)
            return;
        }
    }

    public static CallbackResult<?> beforeCall(Object obj, Class callbackClass, Object ... args) {
        CallbackResult cr = null;
        for (Callback cb : globalCallbacks) {
            if (!ClassUtils.isSubclass(cb.getBaseClass(), callbackClass)) continue;
            try {
                cr = cb.beforeCall(obj, args);
                if (!cr.isBlockingCallbacks()) continue;
                break;
            }
            catch (Exception e) {
                log.error("Exception in global callback", (Throwable)e);
            }
        }
        return cr == null ? CallbackResult.newContinue() : cr;
    }

    public static CallbackResult<?> afterCall(Object obj, Class callbackClass, Object[] args, Object result) {
        CallbackResult cr = null;
        for (Callback cb : globalCallbacks) {
            if (!ClassUtils.isSubclass(cb.getBaseClass(), callbackClass)) continue;
            try {
                cr = cb.afterCall(obj, args, result);
                if (!cr.isBlockingCallbacks()) continue;
                break;
            }
            catch (Exception e) {
                log.error("Exception in global callback", (Throwable)e);
            }
        }
        return cr == null ? CallbackResult.newContinue() : cr;
    }
}

