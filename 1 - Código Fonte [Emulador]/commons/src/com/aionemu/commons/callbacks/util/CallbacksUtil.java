package com.aionemu.commons.callbacks.util;

import com.aionemu.commons.callbacks.Callback;
import com.aionemu.commons.callbacks.CallbackPriority;
import java.lang.annotation.Annotation;
import java.util.List;
import javassist.CtMethod;
import javassist.bytecode.AnnotationsAttribute;

public class CallbacksUtil {
    public static boolean isAnnotationPresent(CtMethod method, Class<? extends Annotation> annotation) {
        for (Object o : method.getMethodInfo().getAttributes()) {
            AnnotationsAttribute attribute;
            if (!(o instanceof AnnotationsAttribute) || (attribute = (AnnotationsAttribute)o).getAnnotation(annotation.getName()) == null) continue;
            return true;
        }
        return false;
    }

    public static int getCallbackPriority(Callback callback) {
        if (callback instanceof CallbackPriority) {
            CallbackPriority instancePriority = (CallbackPriority)((Object)callback);
            return 0 - instancePriority.getPriority();
        }
        return 0;
    }

    protected static void insertCallbackToList(Callback callback, List<Callback> list) {
        int callbackPriority = CallbacksUtil.getCallbackPriority(callback);
        if (!list.isEmpty()) {
            int n = list.size();
            for (int i = 0; i < n; ++i) {
                Callback c = list.get(i);
                int cPrio = CallbacksUtil.getCallbackPriority(c);
                if (callbackPriority >= cPrio) continue;
                list.add(i, callback);
                return;
            }
        }
        list.add(callback);
    }
}

