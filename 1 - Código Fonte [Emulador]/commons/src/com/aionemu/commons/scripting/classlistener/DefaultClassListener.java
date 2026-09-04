package com.aionemu.commons.scripting.classlistener;

import com.aionemu.commons.scripting.classlistener.ClassListener;
import com.aionemu.commons.scripting.metadata.OnClassLoad;
import com.aionemu.commons.scripting.metadata.OnClassUnload;
import java.lang.annotation.Annotation;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DefaultClassListener
implements ClassListener {
    private static final Logger log = LoggerFactory.getLogger(DefaultClassListener.class);

    @Override
    public void postLoad(Class<?>[] classes) {
        for (Class<?> c : classes) {
            this.doMethodInvoke(c.getDeclaredMethods(), OnClassLoad.class);
        }
    }

    @Override
    public void preUnload(Class<?>[] classes) {
        for (Class<?> c : classes) {
            this.doMethodInvoke(c.getDeclaredMethods(), OnClassUnload.class);
        }
    }

    protected final void doMethodInvoke(Method[] methods, Class<? extends Annotation> annotationClass) {
        for (Method m : methods) {
            if (!Modifier.isStatic(m.getModifiers())) continue;
            boolean accessible = m.isAccessible();
            m.setAccessible(true);
            if (m.getAnnotation(annotationClass) != null) {
                try {
                    m.invoke(null, new Object[0]);
                }
                catch (IllegalAccessException e) {
                    log.error("Can't access method " + m.getName() + " of class " + m.getDeclaringClass().getName(), (Throwable)e);
                }
                catch (InvocationTargetException e) {
                    log.error("Can't invoke method " + m.getName() + " of class " + m.getDeclaringClass().getName(), (Throwable)e);
                }
            }
            m.setAccessible(accessible);
        }
    }
}

