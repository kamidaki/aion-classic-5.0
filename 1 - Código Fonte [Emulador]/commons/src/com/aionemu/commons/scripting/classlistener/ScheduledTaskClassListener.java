package com.aionemu.commons.scripting.classlistener;

import com.aionemu.commons.scripting.classlistener.ClassListener;
import com.aionemu.commons.scripting.metadata.Scheduled;
import com.aionemu.commons.services.CronService;
import com.aionemu.commons.utils.ClassUtils;
import java.lang.reflect.Modifier;
import java.util.Map;
import org.quartz.JobDetail;

public class ScheduledTaskClassListener
implements ClassListener {
    @Override
    @SuppressWarnings("unchecked")
    public void postLoad(Class<?>[] classes) {
        for (Class<?> clazz : classes) {
            if (!this.isValidClass(clazz)) continue;
            this.scheduleClass((Class<? extends Runnable>) clazz);
        }
    }

    @Override
    @SuppressWarnings("unchecked")
    public void preUnload(Class<?>[] classes) {
        for (Class<?> clazz : classes) {
            if (!this.isValidClass(clazz)) continue;
            this.unScheduleClass((Class<? extends Runnable>) clazz);
        }
    }

    public boolean isValidClass(Class<?> clazz) {
        if (!ClassUtils.isSubclass(clazz, Runnable.class)) {
            return false;
        }
        int modifiers = clazz.getModifiers();
        if (Modifier.isAbstract(modifiers) || Modifier.isInterface(modifiers)) {
            return false;
        }
        if (!Modifier.isPublic(modifiers)) {
            return false;
        }
        if (!clazz.isAnnotationPresent(Scheduled.class)) {
            return false;
        }
        Scheduled scheduled = clazz.getAnnotation(Scheduled.class);
        if (scheduled.disabled()) {
            return false;
        }
        return scheduled.value().length != 0;
    }

    protected void scheduleClass(Class<? extends Runnable> clazz) {
        Scheduled metadata = clazz.getAnnotation(Scheduled.class);
        try {
            if (metadata.instancePerCronExpression()) {
                for (String s : metadata.value()) {
                    this.getCronService().schedule(clazz.getDeclaredConstructor().newInstance(), s, metadata.longRunningTask());
                }
            } else {
                Runnable r = clazz.getDeclaredConstructor().newInstance();
                for (String s : metadata.value()) {
                    this.getCronService().schedule(r, s, metadata.longRunningTask());
                }
            }
        }
        catch (Exception e) {
            throw new RuntimeException("Failed to schedule runnable " + clazz.getName(), e);
        }
    }

    protected void unScheduleClass(Class<? extends Runnable> clazz) {
        Map<Runnable, JobDetail> map = this.getCronService().getRunnables();
        for (Map.Entry<Runnable, JobDetail> entry : map.entrySet()) {
            if (entry.getKey().getClass() != clazz) continue;
            this.getCronService().cancel(entry.getValue());
        }
    }

    protected CronService getCronService() {
        if (CronService.getInstance() == null) {
            throw new RuntimeException("CronService is not initialized");
        }
        return CronService.getInstance();
    }
}

