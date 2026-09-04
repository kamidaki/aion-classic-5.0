package com.aionemu.commons.utils.i18n;

import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URL;
import java.net.URLConnection;
import java.security.AccessController;
import java.security.PrivilegedActionException;
import java.security.PrivilegedExceptionAction;
import java.util.Locale;
import java.util.PropertyResourceBundle;
import java.util.ResourceBundle;

public class ResourceBundleControl
extends ResourceBundle.Control {
    private String encoding = "UTF-8";

    public ResourceBundleControl() {
    }

    public ResourceBundleControl(String encoding) {
        this.encoding = encoding;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public ResourceBundle newBundle(String baseName, Locale locale, String format, ClassLoader loader, boolean reload) throws IllegalAccessException, InstantiationException, IOException {
        String bundleName = this.toBundleName(baseName, locale);
        ResourceBundle bundle = null;
        if (format.equals("java.class")) {
            try {
                Class<?> bundleClass = loader.loadClass(bundleName);
                if (!ResourceBundle.class.isAssignableFrom(bundleClass)) {
                    throw new ClassCastException(bundleClass.getName() + " cannot be cast to ResourceBundle");
                }
                bundle = (ResourceBundle)bundleClass.newInstance();
            }
            catch (ClassNotFoundException bundleClass) {}
        } else if (format.equals("java.properties")) {
            final String resourceName = this.toResourceName(bundleName, "properties");
            final ClassLoader classLoader = loader;
            final boolean reloadFlag = reload;
            InputStreamReader isr = null;
            try {
                InputStream stream = AccessController.doPrivileged(new PrivilegedExceptionAction<InputStream>(){

                    @Override
                    public InputStream run() throws IOException {
                        InputStream is = null;
                        if (reloadFlag) {
                            URLConnection connection;
                            URL url = classLoader.getResource(resourceName);
                            if (url != null && (connection = url.openConnection()) != null) {
                                connection.setUseCaches(false);
                                is = connection.getInputStream();
                            }
                        } else {
                            is = classLoader.getResourceAsStream(resourceName);
                        }
                        return is;
                    }
                });
                if (stream != null) {
                    isr = new InputStreamReader(stream, this.encoding);
                }
            }
            catch (PrivilegedActionException e) {
                throw (IOException)e.getException();
            }
            if (isr != null) {
                try {
                    bundle = new PropertyResourceBundle(isr);
                }
                finally {
                    isr.close();
                }
            }
        } else {
            throw new IllegalArgumentException("unknown format: " + format);
        }
        return bundle;
    }

    public String getEncoding() {
        return this.encoding;
    }

    public void setEncoding(String encoding) {
        this.encoding = encoding;
    }
}

