package com.aionemu.chatserver;

import ch.qos.logback.classic.LoggerContext;
import ch.qos.logback.classic.joran.JoranConfigurator;
import ch.qos.logback.core.joran.spi.JoranException;
import com.aionemu.chatserver.configs.Config;
import com.aionemu.chatserver.network.netty.NettyServer;
import com.aionemu.chatserver.service.BroadcastService;
import com.aionemu.chatserver.service.ChatService;
import com.aionemu.chatserver.service.GameServerService;
import com.aionemu.chatserver.service.RestartService;
import com.aionemu.chatserver.utils.IdFactory;
import com.aionemu.commons.utils.AEInfos;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.*;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.zip.Deflater;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;


public class ChatServer {

    /**
     * Logger for this class.
     */
    private static final Logger log = LoggerFactory.getLogger(ChatServer.class);

    private static void initalizeLoggger() {
        new File("./log/backup/").mkdirs();
        File[] files = new File("log").listFiles(new FilenameFilter() {
            @Override
            public boolean accept(File dir, String name) {
                return name.endsWith(".log");
            }
        });

        if (files != null && files.length > 0) {
            byte[] buf = new byte[1024];
            String outFilename = "./log/backup/" + new SimpleDateFormat("yyyy-MM-dd HHmmss").format(new Date()) + ".zip";
            try (ZipOutputStream out = new ZipOutputStream(new FileOutputStream(outFilename))) {
                out.setMethod(ZipOutputStream.DEFLATED);
                out.setLevel(Deflater.BEST_COMPRESSION);

                for (File logFile : files) {
                    try (FileInputStream in = new FileInputStream(logFile)) {
                        out.putNextEntry(new ZipEntry(logFile.getName()));
                        int len;
                        while ((len = in.read(buf)) > 0) {
                            out.write(buf, 0, len);
                        }
                        out.closeEntry();
                    }
                    logFile.delete();
                }
            } catch (IOException ignored) {
            }
        }
        LoggerContext lc = (LoggerContext) LoggerFactory.getILoggerFactory();
        try {
            JoranConfigurator configurator = new JoranConfigurator();
            configurator.setContext(lc);
            lc.reset();
            configurator.doConfigure("config/slf4j-logback.xml");
        } catch (JoranException je) {
            throw new RuntimeException("Failed to configure loggers, shutting down...", je);
        }
    }

    /**
     * @param args
     */
    public static void main(String[] args) {
        long start = System.currentTimeMillis();

        initalizeLoggger();

        Config.load();
        AEInfos.printAllInfos();
        IdFactory.getInstance();
        GameServerService.getInstance();
        BroadcastService.getInstance();
        ChatService.getInstance();
        NettyServer.getInstance();
        RestartService.getInstance();

        Runtime.getRuntime().addShutdownHook(ShutdownHook.getInstance());
        log.info("AL ChatServer started in " + (System.currentTimeMillis() - start) / 1000 + " seconds.");
        System.out.println(
                "    ___    ________  _   __   ________    ___   __________ __________\n" +
                "   /   |  /  _/ __ \\/ | / /  / ____/ /   /   | / ___/ ___//  _/ ____/\n" +
                "  / /| |  / // / / /  |/ /  / /   / /   / /| | \\__ \\\\__ \\ / // /     \n" +
                " / ___ |_/ // /_/ / /|  /  / /___/ /___/ ___ |___/ /__/ // // /___   \n" +
                "/_/  |_/___/\\____/_/ |_/   \\____/_____/_/  |_/____/____/___/\\____/   ");
        System.out.println("                        Versão 5.0 EU (GameForge)");
        System.out.println("               Desenvolvido por: Lost Academy Team & Durak\n");
    }
}
