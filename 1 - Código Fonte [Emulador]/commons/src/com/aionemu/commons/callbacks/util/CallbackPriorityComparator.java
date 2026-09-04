package com.aionemu.commons.callbacks.util;

import com.aionemu.commons.callbacks.Callback;
import com.aionemu.commons.callbacks.util.CallbacksUtil;
import java.util.Comparator;

public class CallbackPriorityComparator
implements Comparator<Callback<?>> {
    @Override
    public int compare(Callback<?> o1, Callback<?> o2) {
        int p2;
        int p1 = CallbacksUtil.getCallbackPriority(o1);
        if (p1 < (p2 = CallbacksUtil.getCallbackPriority(o2))) {
            return -1;
        }
        if (p1 == p2) {
            return 0;
        }
        return 1;
    }
}

