package com.aionemu.commons.network.util;

import com.aionemu.commons.network.util.DeadLockDetector;
import com.aionemu.commons.utils.concurrent.PriorityThreadFactory;
import com.aionemu.commons.utils.concurrent.RunnableWrapper;
import com.google.common.util.concurrent.JdkFutureAdapters;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.common.util.concurrent.ListeningExecutorService;
import com.google.common.util.concurrent.ListeningScheduledExecutorService;
import com.google.common.util.concurrent.MoreExecutors;
import java.util.concurrent.Executor;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledThreadPoolExecutor;
import java.util.concurrent.SynchronousQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ThreadPoolManager
implements Executor {
    private static final Logger log = LoggerFactory.getLogger(ThreadPoolManager.class);
    private ScheduledThreadPoolExecutor scheduledThreadPoolExecutor;
    private ListeningScheduledExecutorService scheduledThreadPool;
    private final ThreadPoolExecutor generalPacketsThreadPoolExecutor;
    private final ListeningExecutorService generalPacketsThreadPool;

    public static final ThreadPoolManager getInstance() {
        return SingletonHolder.instance;
    }

    private ThreadPoolManager() {
        new DeadLockDetector(60, DeadLockDetector.RESTART).start();
        this.scheduledThreadPoolExecutor = new ScheduledThreadPoolExecutor(4, new PriorityThreadFactory("ScheduledThreadPool", 5));
        this.scheduledThreadPool = MoreExecutors.listeningDecorator((ScheduledExecutorService)this.scheduledThreadPoolExecutor);
        this.generalPacketsThreadPoolExecutor = new ThreadPoolExecutor(1, Integer.MAX_VALUE, 60L, TimeUnit.SECONDS, new SynchronousQueue<Runnable>());
        this.generalPacketsThreadPool = MoreExecutors.listeningDecorator((ExecutorService)this.generalPacketsThreadPoolExecutor);
    }

    @Override
    public void execute(Runnable pkt) {
        this.generalPacketsThreadPool.execute((Runnable)new RunnableWrapper(pkt));
    }

    public ListeningExecutorService getPacketsThreadPool() {
        return this.generalPacketsThreadPool;
    }

    public <T extends Runnable> ListenableFuture<T> schedule(T r, long delay) {
        try {
            if (delay < 0L) {
                delay = 0L;
            }
            return JdkFutureAdapters.listenInPoolThread((Future)this.scheduledThreadPool.schedule(r, delay, TimeUnit.MILLISECONDS));
        }
        catch (RejectedExecutionException e) {
            return null;
        }
    }

    public <T extends Runnable> ListenableFuture<T> scheduleAtFixedRate(T r, long initial, long delay) {
        try {
            if (delay < 0L) {
                delay = 0L;
            }
            if (initial < 0L) {
                initial = 0L;
            }
            return JdkFutureAdapters.listenInPoolThread((Future)this.scheduledThreadPool.scheduleAtFixedRate(r, initial, delay, TimeUnit.MILLISECONDS));
        }
        catch (RejectedExecutionException e) {
            return null;
        }
    }

    public void shutdown() {
        try {
            this.scheduledThreadPool.shutdown();
            this.generalPacketsThreadPool.shutdown();
            this.scheduledThreadPool.awaitTermination(2L, TimeUnit.SECONDS);
            this.generalPacketsThreadPool.awaitTermination(2L, TimeUnit.SECONDS);
            log.info("All ThreadPools are now stopped.");
        }
        catch (InterruptedException e) {
            log.error("Can't shutdown ThreadPoolManager", (Throwable)e);
        }
    }

    private static class SingletonHolder {
        protected static final ThreadPoolManager instance = new ThreadPoolManager();

        private SingletonHolder() {
        }
    }
}

