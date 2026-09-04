package com.aionemu.commons.utils;

import java.lang.annotation.Annotation;
import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ClassUtil {
    private static final Logger log = LoggerFactory.getLogger(ClassUtil.class);

    public static Optional<Object> singletonInstance(Class<?> clazz) {
        try {
            Method method = clazz.getDeclaredMethod("getInstance", new Class[0]);
            return Optional.of(method.invoke(null, new Object[0]));
        }
        catch (NoSuchMethodException e) {
            log.debug("Class {} don't have getInstance method", clazz, (Object)e);
            return Optional.empty();
        }
        catch (Exception e) {
            log.error("Error while instantiating singleton instance of " + clazz.getSimpleName(), (Throwable)e);
            return Optional.empty();
        }
    }

    public static Optional<Object> singletonOrNewInstance(Class<?> clazz) {
        Optional<Object> instance = ClassUtil.singletonInstance(clazz);
        return instance == null ? ClassUtil.newInstance(clazz) : instance;
    }

    public static Optional<Object> newInstance(Class<?> clazz) {
        try {
            Constructor<?> constructor = clazz.getDeclaredConstructor(new Class[0]);
            constructor.setAccessible(true);
            return Optional.of(constructor.newInstance(new Object[0]));
        }
        catch (NoSuchMethodException e) {
            log.debug("Class {} don't have default constructor method", clazz, (Object)e);
            return Optional.empty();
        }
        catch (Exception e) {
            log.error("Error while instantiating singleton instance of " + clazz.getSimpleName(), (Throwable)e);
            return Optional.empty();
        }
    }

    public static List<Method> getMethodsAnnotatedWith(Class<?> type, Class<? extends Annotation> annotation) {
        ArrayList<Method> methods = new ArrayList<Method>();
        for (Class<?> klass = type; klass != Object.class; klass = klass.getSuperclass()) {
            ArrayList<Method> allMethods = new ArrayList<Method>(Arrays.asList(klass.getDeclaredMethods()));
            methods.addAll(allMethods.stream().filter(method -> method.isAnnotationPresent(annotation)).collect(Collectors.toList()));
        }
        return methods;
    }

    public static Optional<Method> getMethodWithAnnotatedParameter(Class<?> clazz, Class<?> annotation, Class<?> type) {
        return Arrays.stream(clazz.getDeclaredMethods()).filter(method -> method.getParameterAnnotations().length > 0).filter(method -> method.getParameterTypes()[0].equals(type)).filter(method -> Arrays.stream(method.getParameterAnnotations()).filter(x -> ((Annotation[])x).length == 1).map(x -> x[0]).anyMatch(x -> x.annotationType().equals(annotation))).findFirst();
    }
}

