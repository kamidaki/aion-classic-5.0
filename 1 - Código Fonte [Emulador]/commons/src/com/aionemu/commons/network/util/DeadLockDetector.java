package com.aionemu.commons.network.util;

import java.lang.management.LockInfo;
import java.lang.management.ManagementFactory;
import java.lang.management.MonitorInfo;
import java.lang.management.ThreadInfo;
import java.lang.management.ThreadMXBean;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DeadLockDetector
extends Thread {
    private static final Logger log = LoggerFactory.getLogger(DeadLockDetector.class);
    public static final byte NOTHING = 0;
    public static final byte RESTART = 1;
    private final int sleepTime;
    private final ThreadMXBean tmx;
    private final byte doWhenDL;

    public DeadLockDetector(int sleepTime, byte doWhenDL) {
        super("DeadLockDetector");
        this.sleepTime = sleepTime * 1000;
        this.tmx = ManagementFactory.getThreadMXBean();
        this.doWhenDL = doWhenDL;
    }

    @Override
    public final void run() {
        boolean deadlock = false;
        while (!deadlock) {
            try {
                long[] ids = this.tmx.findDeadlockedThreads();
                if (ids != null) {
                    deadlock = true;
                    ThreadInfo[] tis = this.tmx.getThreadInfo(ids, true, true);
                    String info = "DeadLock Found!\n";
                    for (ThreadInfo ti : tis) {
                        info = info + ti.toString();
                    }
                    for (ThreadInfo ti : tis) {
                        LockInfo[] locks = ti.getLockedSynchronizers();
                        MonitorInfo[] monitors = ti.getLockedMonitors();
                        if (locks.length == 0 && monitors.length == 0) continue;
                        ThreadInfo dl = ti;
                        info = info + "Java-level deadlock:\n";
                        info = info + this.createShortLockInfo(dl);
                        while ((dl = this.tmx.getThreadInfo(new long[]{dl.getLockOwnerId()}, true, true)[0]).getThreadId() != ti.getThreadId()) {
                            info = info + this.createShortLockInfo(dl);
                        }
                        info = info + "\nDumping all threads:\n";
                        for (ThreadInfo dumpedTI : this.tmx.dumpAllThreads(true, true)) {
                            info = info + this.printDumpedThreadInfo(dumpedTI);
                        }
                    }
                    log.warn(info);
                    if (this.doWhenDL == 1) {
                        System.exit(2);
                    }
                }
                Thread.sleep(this.sleepTime);
            }
            catch (Exception e) {
                log.warn("DeadLockDetector: " + e, (Throwable)e);
            }
        }
    }

    private String createShortLockInfo(ThreadInfo threadInfo) {
        StringBuilder sb = new StringBuilder("\t");
        sb.append(threadInfo.getThreadName());
        sb.append(" is waiting to lock ");
        sb.append(threadInfo.getLockInfo().toString());
        sb.append(" which is held by ");
        sb.append(threadInfo.getLockOwnerName());
        sb.append(". Locked synchronizers:");
        sb.append(threadInfo.getLockedSynchronizers().length);
        sb.append(" monitors:");
        sb.append(threadInfo.getLockedMonitors().length);
        sb.append("\n");
        return sb.toString();
    }

    private String printDumpedThreadInfo(ThreadInfo threadInfo) {
        StringBuilder sb = new StringBuilder();
        sb.append("\n\"" + threadInfo.getThreadName() + "\" Id=" + threadInfo.getThreadId() + " " + (Object)((Object)threadInfo.getThreadState()) + "\n");
        StackTraceElement[] stacktrace = threadInfo.getStackTrace();
        for (int i = 0; i < stacktrace.length; ++i) {
            StackTraceElement ste = stacktrace[i];
            sb.append("\tat " + ste.toString() + "\n");
            for (MonitorInfo mi : threadInfo.getLockedMonitors()) {
                if (mi.getLockedStackDepth() != i) continue;
                sb.append("\t-  locked " + mi);
                sb.append('\n');
            }
        }
        return sb.toString();
    }
}

