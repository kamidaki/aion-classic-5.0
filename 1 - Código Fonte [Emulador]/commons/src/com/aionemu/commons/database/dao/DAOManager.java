package com.aionemu.commons.database.dao;

import com.aionemu.commons.configs.DatabaseConfig;
import com.aionemu.commons.database.DatabaseFactory;
import com.aionemu.commons.database.dao.DAO;
import com.aionemu.commons.database.dao.DAOAlreadyRegisteredException;
import com.aionemu.commons.database.dao.DAOLoader;
import com.aionemu.commons.database.dao.DAONotFoundException;
import com.aionemu.commons.scripting.classlistener.AggregatedClassListener;
import com.aionemu.commons.scripting.classlistener.OnClassLoadUnloadListener;
import com.aionemu.commons.scripting.classlistener.ScheduledTaskClassListener;
import com.aionemu.commons.scripting.scriptmanager.ScriptManager;
import java.io.FileNotFoundException;
import java.util.HashMap;
import java.util.Map;
import javax.xml.bind.JAXBException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DAOManager {
    private static final Logger log = LoggerFactory.getLogger(DAOManager.class);
    private static final Map<String, DAO> daoMap = new HashMap<String, DAO>();
    private static ScriptManager scriptManager;

    public static void init() {
        try {
            scriptManager = new ScriptManager();
            AggregatedClassListener acl = new AggregatedClassListener();
            acl.addClassListener(new OnClassLoadUnloadListener());
            acl.addClassListener(new ScheduledTaskClassListener());
            acl.addClassListener(new DAOLoader());
            scriptManager.setGlobalClassListener(acl);
            scriptManager.load(DatabaseConfig.DATABASE_SCRIPTCONTEXT_DESCRIPTOR);
        }
        catch (RuntimeException e) {
            throw new Error(e.getMessage(), e);
        }
        catch (FileNotFoundException e) {
            throw new Error("Can't load database script context: " + DatabaseConfig.DATABASE_SCRIPTCONTEXT_DESCRIPTOR, e);
        }
        catch (JAXBException e) {
            throw new Error("Can't compile database handlers - check your MySQL5 implementations", e);
        }
        catch (Exception e) {
            throw new Error("A fatal error occured during loading or compiling the database handlers", e);
        }
        log.info("Loaded " + daoMap.size() + " DAO implementations.");
    }

    public static void shutdown() {
        scriptManager.shutdown();
        daoMap.clear();
        scriptManager = null;
    }

    public static <T extends DAO> T getDAO(Class<T> clazz) throws DAONotFoundException {
        DAO result = daoMap.get(clazz.getName());
        if (result == null) {
            String s = "DAO for class " + clazz.getSimpleName() + " not implemented";
            log.error(s);
            throw new DAONotFoundException(s);
        }
        return (T)result;
    }

    public static void registerDAO(Class<? extends DAO> daoClass) throws DAOAlreadyRegisteredException, Exception {
        DAO dao;
        try {
            dao = daoClass.getDeclaredConstructor().newInstance();
        } catch (Exception e) {
            log.error("Can't instantiate DAO: " + daoClass.getName(), e);
            return;
        }
        if (!dao.supports(DatabaseFactory.getDatabaseName(), DatabaseFactory.getDatabaseMajorVersion(), DatabaseFactory.getDatabaseMinorVersion())) {
            return;
        }
        synchronized (DAOManager.class) {
            DAO oldDao = daoMap.get(dao.getClassName());
            if (oldDao != null) {
                StringBuilder sb = new StringBuilder();
                sb.append("DAO with className ").append(dao.getClassName()).append(" is used by ");
                sb.append(oldDao.getClass().getName()).append(". Can't override with ");
                sb.append(daoClass.getName()).append(".");
                String s = sb.toString();
                log.error(s);
                throw new DAOAlreadyRegisteredException(s);
            }
            daoMap.put(dao.getClassName(), dao);
            if (log.isDebugEnabled()) {
                log.debug("DAO " + dao.getClassName() + " was successfully registered.");
            }
        }
    }

    public static void unregisterDAO(Class<? extends DAO> daoClass) {
        synchronized (DAOManager.class) {
            for (DAO dao : daoMap.values()) {
                if (dao.getClass() != daoClass) continue;
                daoMap.remove(dao.getClassName());
                if (log.isDebugEnabled()) {
                    log.debug("DAO " + dao.getClassName() + " was successfully unregistered.");
                }
                break;
            }
        }
    }

    private DAOManager() {
    }
}

