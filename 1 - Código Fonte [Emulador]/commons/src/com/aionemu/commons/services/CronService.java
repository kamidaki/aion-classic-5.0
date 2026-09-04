package com.aionemu.commons.services;

import com.aionemu.commons.services.cron.CronServiceException;
import com.aionemu.commons.services.cron.RunnableRunner;
import com.aionemu.commons.utils.GenericValidator;
import com.google.common.collect.Maps;
import com.google.common.collect.Sets;
import java.util.Collection;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Set;
import org.quartz.CronScheduleBuilder;
import org.quartz.CronTrigger;
import org.quartz.JobBuilder;
import org.quartz.JobDataMap;
import org.quartz.JobDetail;
import org.quartz.JobKey;
import org.quartz.ScheduleBuilder;
import org.quartz.Scheduler;
import org.quartz.SchedulerException;
import org.quartz.Trigger;
import org.quartz.TriggerBuilder;
import org.quartz.impl.StdSchedulerFactory;
import org.quartz.impl.matchers.GroupMatcher;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public final class CronService {
    private static final Logger log = LoggerFactory.getLogger(CronService.class);
    private static CronService instance;
    private Scheduler scheduler;
    private Class<? extends RunnableRunner> runnableRunner;

    public static CronService getInstance() {
        return instance;
    }

    public static synchronized void initSingleton(Class<? extends RunnableRunner> runableRunner) {
        if (instance != null) {
            throw new CronServiceException("CronService is already initialized");
        }
        CronService cs = new CronService();
        cs.init(runableRunner);
        instance = cs;
    }

    private CronService() {
    }

    public synchronized void init(Class<? extends RunnableRunner> runnableRunner) {
        if (this.scheduler != null) {
            return;
        }
        if (runnableRunner == null) {
            throw new CronServiceException("RunnableRunner class must be defined");
        }
        this.runnableRunner = runnableRunner;
        Properties properties = new Properties();
        properties.setProperty("org.quartz.threadPool.threadCount", "1");
        try {
            this.scheduler = new StdSchedulerFactory(properties).getScheduler();
            this.scheduler.start();
        }
        catch (SchedulerException e) {
            throw new CronServiceException("Failed to initialize CronService", e);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void shutdown() {
        Scheduler localScheduler;
        CronService cronService = this;
        synchronized (cronService) {
            if (this.scheduler == null) {
                return;
            }
            localScheduler = this.scheduler;
            this.scheduler = null;
            this.runnableRunner = null;
        }
        try {
            localScheduler.shutdown(false);
        }
        catch (SchedulerException e) {
            log.error("Failed to shutdown CronService correctly", (Throwable)e);
        }
    }

    public void schedule(Runnable r, String cronExpression) {
        this.schedule(r, cronExpression, false);
    }

    public void schedule(Runnable r, String cronExpression, boolean longRunning) {
        try {
            JobDataMap jdm = new JobDataMap();
            jdm.put("cronservice.scheduled.runnable.instance", (Object)r);
            jdm.put("cronservice.scheduled.runnable.islognrunning", longRunning);
            jdm.put("cronservice.scheduled.runnable.cronexpression", cronExpression);
            String jobId = "Started at ms" + System.currentTimeMillis() + "; ns" + System.nanoTime();
            JobKey jobKey = new JobKey("JobKey:" + jobId);
            JobDetail jobDetail = JobBuilder.newJob(this.runnableRunner).usingJobData(jdm).withIdentity(jobKey).build();
            CronScheduleBuilder csb = CronScheduleBuilder.cronSchedule((String)cronExpression);
            CronTrigger trigger = (CronTrigger)TriggerBuilder.newTrigger().withSchedule((ScheduleBuilder)csb).build();
            this.scheduler.scheduleJob(jobDetail, (Trigger)trigger);
        }
        catch (Exception e) {
            throw new CronServiceException("Failed to start job", e);
        }
    }

    public void cancel(Runnable r) {
        Map<Runnable, JobDetail> map = this.getRunnables();
        JobDetail jd = map.get(r);
        this.cancel(jd);
    }

    public void cancel(JobDetail jd) {
        if (jd == null) {
            return;
        }
        if (jd.getKey() == null) {
            throw new CronServiceException("JobDetail should have JobKey");
        }
        try {
            this.scheduler.deleteJob(jd.getKey());
        }
        catch (SchedulerException e) {
            throw new CronServiceException("Failed to delete Job", e);
        }
    }

    protected Collection<JobDetail> getJobDetails() {
        if (this.scheduler == null) {
            return Collections.emptySet();
        }
        try {
            Set<JobKey> keys = this.scheduler.getJobKeys(GroupMatcher.anyJobGroup());
            if (GenericValidator.isBlankOrNull(keys)) {
                return Collections.emptySet();
            }
            Set<JobDetail> result = Sets.newHashSetWithExpectedSize(keys.size());
            for (JobKey jk : keys) {
                result.add(this.scheduler.getJobDetail(jk));
            }
            return result;
        }
        catch (Exception e) {
            throw new CronServiceException("Can't get all active job details", e);
        }
    }

    public Map<Runnable, JobDetail> getRunnables() {
        Collection<JobDetail> jobDetails = this.getJobDetails();
        if (GenericValidator.isBlankOrNull(jobDetails)) {
            return Collections.emptyMap();
        }
        HashMap result = Maps.newHashMap();
        for (JobDetail jd : jobDetails) {
            if (GenericValidator.isBlankOrNull(jd.getJobDataMap()) || !jd.getJobDataMap().containsKey((Object)"cronservice.scheduled.runnable.instance")) continue;
            result.put((Runnable)jd.getJobDataMap().get((Object)"cronservice.scheduled.runnable.instance"), jd);
        }
        return Collections.unmodifiableMap(result);
    }

    public List<? extends Trigger> getJobTriggers(JobDetail jd) {
        return this.getJobTriggers(jd.getKey());
    }

    public List<? extends Trigger> getJobTriggers(JobKey jk) {
        if (this.scheduler == null) {
            return Collections.emptyList();
        }
        try {
            return this.scheduler.getTriggersOfJob(jk);
        }
        catch (SchedulerException e) {
            throw new CronServiceException("Can't get triggers for JobKey " + jk, e);
        }
    }
}

