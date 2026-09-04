package com.aionl.slf4j.conversion;

import ch.qos.logback.core.FileAppender;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.IOException;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;
import org.apache.commons.io.FileUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TruncateToZipFileAppender
extends FileAppender<Object> {
    private static final Logger log = LoggerFactory.getLogger(TruncateToZipFileAppender.class);
    private String backupDir = "log/backup";

    public void openFile(String fname) throws IOException {
        File file = new File(fname);
        if (file.exists()) {
            this.truncate(file);
        }
        super.openFile(fname);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    protected void truncate(File file) {
        File backupRoot = new File(this.backupDir);
        if (!backupRoot.exists() && !backupRoot.mkdirs()) {
            log.warn("Can't create backup dir for backup storage");
            return;
        }
        String date = "";
        try {
            BufferedReader reader = new BufferedReader(new FileReader(file));
            date = reader.readLine().split("\f")[1];
            reader.close();
        }
        catch (IOException e) {
            e.printStackTrace();
        }
        File zipFile = new File(backupRoot, file.getName() + "." + date + ".zip");
        ZipOutputStream zos = null;
        FileInputStream fis = null;
        try {
            int readed;
            zos = new ZipOutputStream(new FileOutputStream(zipFile));
            ZipEntry entry = new ZipEntry(file.getName());
            entry.setMethod(8);
            entry.setCrc(FileUtils.checksumCRC32((File)file));
            zos.putNextEntry(entry);
            fis = FileUtils.openInputStream((File)file);
            byte[] buffer = new byte[1024];
            while ((readed = fis.read(buffer)) != -1) {
                zos.write(buffer, 0, readed);
            }
        }
        catch (Exception e) {
            log.warn("Can't create zip file", (Throwable)e);
        }
        finally {
            if (zos != null) {
                try {
                    zos.close();
                }
                catch (IOException e) {
                    log.warn("Can't close zip file", (Throwable)e);
                }
            }
            if (fis != null) {
                try {
                    fis.close();
                }
                catch (IOException e) {
                    log.warn("Can't close zipped file", (Throwable)e);
                }
            }
        }
        if (!file.delete()) {
            log.warn("Can't delete old log file " + file.getAbsolutePath());
        }
    }
}

