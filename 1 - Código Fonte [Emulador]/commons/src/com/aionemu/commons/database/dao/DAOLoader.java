package com.aionemu.commons.database.dao;

import com.aionemu.commons.database.dao.DAO;
import com.aionemu.commons.database.dao.DAOManager;
import com.aionemu.commons.database.dao.DisabledDAO;
import com.aionemu.commons.scripting.classlistener.ClassListener;
import com.aionemu.commons.utils.ClassUtils;
import java.lang.reflect.Modifier;

public class DAOLoader
implements ClassListener {
    @Override
    @SuppressWarnings("unchecked")
    public void postLoad(Class<?>[] classes) {
        for (Class<?> clazz : classes) {
            if (!this.isValidDAO(clazz)) continue;
            try {
                DAOManager.registerDAO((Class<? extends DAO>) clazz);
            }
            catch (Exception e) {
                throw new Error("Can't register DAO class", e);
            }
        }
    }

    @Override
    @SuppressWarnings("unchecked")
    public void preUnload(Class<?>[] classes) {
        for (Class<?> clazz : classes) {
            if (!this.isValidDAO(clazz)) continue;
            try {
                DAOManager.unregisterDAO((Class<? extends DAO>) clazz);
            }
            catch (Exception e) {
                throw new Error("Can't unregister DAO class", e);
            }
        }
    }

    public boolean isValidDAO(Class<?> clazz) {
        if (!ClassUtils.isSubclass(clazz, DAO.class)) {
            return false;
        }
        int modifiers = clazz.getModifiers();
        if (Modifier.isAbstract(modifiers) || Modifier.isInterface(modifiers)) {
            return false;
        }
        if (!Modifier.isPublic(modifiers)) {
            return false;
        }
        return !clazz.isAnnotationPresent(DisabledDAO.class);
    }
}

