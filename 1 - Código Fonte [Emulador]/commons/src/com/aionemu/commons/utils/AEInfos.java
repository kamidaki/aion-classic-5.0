package com.aionemu.commons.utils;

import java.text.DecimalFormat;
import java.text.SimpleDateFormat;
import java.util.Date;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AEInfos {
    private static final Logger log = LoggerFactory.getLogger(AEInfos.class);

    public static String[] getMemoryInfo() {
        double max = Runtime.getRuntime().maxMemory() / 1024L;
        double allocated = Runtime.getRuntime().totalMemory() / 1024L;
        double nonAllocated = max - allocated;
        double cached = Runtime.getRuntime().freeMemory() / 1024L;
        double used = allocated - cached;
        double useable = max - used;
        DecimalFormat df = new DecimalFormat(" (0.0000'%')");
        DecimalFormat df2 = new DecimalFormat(" # 'KB'");
        return new String[]{"+----", "| Global Memory Informations at " + AEInfos.getRealTime().toString() + ":", "|    |", "| Allowed Memory:" + df2.format(max), "|    |= Allocated Memory:" + df2.format(allocated) + df.format(allocated / max * 100.0), "|    |= Non-Allocated Memory:" + df2.format(nonAllocated) + df.format(nonAllocated / max * 100.0), "| Allocated Memory:" + df2.format(allocated), "|    |= Used Memory:" + df2.format(used) + df.format(used / max * 100.0), "|    |= Unused (cached) Memory:" + df2.format(cached) + df.format(cached / max * 100.0), "| Useable Memory:" + df2.format(useable) + df.format(useable / max * 100.0), "+----"};
    }

    public static String[] getCPUInfo() {
        return new String[]{"Available CPU(s): " + Runtime.getRuntime().availableProcessors(), "Processor(s) Identifier: " + System.getenv("PROCESSOR_IDENTIFIER"), "..................................................", ".................................................."};
    }

    public static String[] getOSInfo() {
        return new String[]{"OS: " + System.getProperty("os.name") + " Build: " + System.getProperty("os.version"), "OS Arch: " + System.getProperty("os.arch"), "..................................................", ".................................................."};
    }

    public static String[] getJREInfo() {
        return new String[]{"Java Platform Information", "Java Runtime  Name: " + System.getProperty("java.runtime.name"), "Java Version: " + System.getProperty("java.version"), "Java Class Version: " + System.getProperty("java.class.version"), "..................................................", ".................................................."};
    }

    public static String[] getJVMInfo() {
        return new String[]{"Virtual Machine Information (JVM)", "JVM Name: " + System.getProperty("java.vm.name"), "JVM installation directory: " + System.getProperty("java.home"), "JVM version: " + System.getProperty("java.vm.version"), "JVM Vendor: " + System.getProperty("java.vm.vendor"), "JVM Info: " + System.getProperty("java.vm.info"), "..................................................", ".................................................."};
    }

    public static String getRealTime() {
        SimpleDateFormat String2 = new SimpleDateFormat("H:mm:ss");
        return String2.format(new Date());
    }

    public static void printMemoryInfo() {
        for (String line : AEInfos.getMemoryInfo()) {
            log.info(line);
        }
    }

    public static void printCPUInfo() {
        for (String line : AEInfos.getCPUInfo()) {
            log.info(line);
        }
    }

    public static void printOSInfo() {
        for (String line : AEInfos.getOSInfo()) {
            log.info(line);
        }
    }

    public static void printJREInfo() {
        for (String line : AEInfos.getJREInfo()) {
            log.info(line);
        }
    }

    public static void printJVMInfo() {
        for (String line : AEInfos.getJVMInfo()) {
            log.info(line);
        }
    }

    public static void printRealTime() {
        log.info(AEInfos.getRealTime().toString());
    }

    public static void printAllInfos() {
        AEInfos.printOSInfo();
        AEInfos.printCPUInfo();
        AEInfos.printJREInfo();
        AEInfos.printJVMInfo();
        AEInfos.printMemoryInfo();
    }
}

