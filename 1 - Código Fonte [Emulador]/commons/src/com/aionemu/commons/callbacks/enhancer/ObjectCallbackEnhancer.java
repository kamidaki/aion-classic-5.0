package com.aionemu.commons.callbacks.enhancer;

import com.aionemu.commons.callbacks.Callback;
import com.aionemu.commons.callbacks.CallbackResult;
import com.aionemu.commons.callbacks.EnhancedObject;
import com.aionemu.commons.callbacks.enhancer.CallbackClassFileTransformer;
import com.aionemu.commons.callbacks.metadata.ObjectCallback;
import com.aionemu.commons.callbacks.util.CallbacksUtil;
import com.aionemu.commons.callbacks.util.ObjectCallbackHelper;
import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.util.HashSet;
import java.util.Map;
import java.util.concurrent.locks.ReentrantReadWriteLock;
import javassist.CannotCompileException;
import javassist.ClassPath;
import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtField;
import javassist.CtMethod;
import javassist.LoaderClassPath;
import javassist.Modifier;
import javassist.NotFoundException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ObjectCallbackEnhancer
extends CallbackClassFileTransformer {
    private static final Logger log = LoggerFactory.getLogger(ObjectCallbackEnhancer.class);
    public static final String FIELD_NAME_CALLBACKS = "$$$callbacks";
    public static final String FIELD_NAME_CALLBACKS_LOCK = "$$$callbackLock";

    @Override
    protected byte[] transformClass(ClassLoader loader, byte[] clazzBytes) throws Exception {
        ClassPool cp = new ClassPool();
        cp.appendClassPath((ClassPath)new LoaderClassPath(loader));
        CtClass clazz = cp.makeClass((InputStream)new ByteArrayInputStream(clazzBytes));
        HashSet<CtMethod> methdosToEnhance = new HashSet<CtMethod>();
        for (CtMethod method : clazz.getDeclaredMethods()) {
            if (!this.isEnhanceable(method)) continue;
            methdosToEnhance.add(method);
        }
        if (!methdosToEnhance.isEmpty()) {
            CtClass eo = cp.get(EnhancedObject.class.getName());
            for (CtClass i : clazz.getInterfaces()) {
                if (!i.equals(eo)) continue;
                throw new RuntimeException("Class already implements EnhancedObject interface, WTF???");
            }
            log.debug("Enhancing class: " + clazz.getName());
            this.writeEnhancedObjectImpl(clazz);
            for (CtMethod method : methdosToEnhance) {
                log.debug("Enhancing method: " + method.getLongName());
                this.enhanceMethod(method);
            }
            return clazz.toBytecode();
        }
        log.trace("Class " + clazz.getName() + " was not enhanced");
        return null;
    }

    protected void enhanceMethod(CtMethod method) throws CannotCompileException, NotFoundException, ClassNotFoundException {
        ClassPool cp = method.getDeclaringClass().getClassPool();
        method.addLocalVariable("___cbr", cp.get(CallbackResult.class.getName()));
        CtClass listenerClazz = cp.get(((ObjectCallback)method.getAnnotation(ObjectCallback.class)).value().getName());
        String listenerFieldName = "$$$" + listenerClazz.getSimpleName();
        CtClass clazz = method.getDeclaringClass();
        try {
            clazz.getField(listenerFieldName);
        }
        catch (NotFoundException e) {
            clazz.addField(CtField.make((String)("Class " + listenerFieldName + " = Class.forName(\"" + listenerClazz.getName() + "\");"), (CtClass)clazz));
        }
        int paramLength = method.getParameterTypes().length;
        method.insertBefore(this.writeBeforeMethod(method, paramLength, listenerFieldName));
        method.insertAfter(this.writeAfterMethod(method, paramLength, listenerFieldName));
    }

    protected String writeBeforeMethod(CtMethod method, int paramLength, String listenerFieldName) throws NotFoundException, CannotCompileException {
        StringBuilder sb = new StringBuilder();
        sb.append('{');
        sb.append(" ___cbr = ");
        sb.append(ObjectCallbackHelper.class.getName()).append(".beforeCall((");
        sb.append(EnhancedObject.class.getName());
        sb.append(")this, " + listenerFieldName + ", ");
        if (paramLength > 0) {
            sb.append("new Object[]{");
            for (int i = 1; i <= paramLength; ++i) {
                sb.append("($w)$").append(i);
                if (i >= paramLength) continue;
                sb.append(',');
            }
            sb.append("}");
        } else {
            sb.append("null");
        }
        sb.append(");");
        sb.append("if(___cbr.isBlockingCaller()){");
        CtClass returnType = method.getReturnType();
        if (returnType.equals(CtClass.voidType)) {
            sb.append("return");
        } else if (returnType.equals(CtClass.booleanType)) {
            sb.append("return false");
        } else if (returnType.equals(CtClass.charType)) {
            sb.append("return 'a'");
        } else if (returnType.equals(CtClass.byteType) || returnType.equals(CtClass.shortType) || returnType.equals(CtClass.intType) || returnType.equals(CtClass.floatType) || returnType.equals(CtClass.longType) || returnType.equals(CtClass.longType)) {
            sb.append("return 0");
        }
        sb.append(";}}");
        return sb.toString();
    }

    protected String writeAfterMethod(CtMethod method, int paramLength, String listenerFieldName) throws NotFoundException {
        StringBuilder sb = new StringBuilder();
        sb.append('{');
        if (!method.getReturnType().equals(CtClass.voidType)) {
            sb.append("if(___cbr.isBlockingCaller()){");
            sb.append("$_ = ($r)($w)___cbr.getResult();");
            sb.append("}");
        }
        sb.append("___cbr = ").append(ObjectCallbackHelper.class.getName()).append(".afterCall((");
        sb.append(EnhancedObject.class.getName()).append(")this, " + listenerFieldName + ", ");
        if (paramLength > 0) {
            sb.append("new Object[]{");
            for (int i = 1; i <= paramLength; ++i) {
                sb.append("($w)$").append(i);
                if (i >= paramLength) continue;
                sb.append(',');
            }
            sb.append("}");
        } else {
            sb.append("null");
        }
        sb.append(", ($w)$_);");
        sb.append("if(___cbr.isBlockingCaller()){");
        if (method.getReturnType().equals(CtClass.voidType)) {
            sb.append("return;");
        } else {
            sb.append("return ($r)($w)___cbr.getResult();");
        }
        sb.append("}");
        sb.append("else {return $_;}");
        sb.append("}");
        return sb.toString();
    }

    protected void writeEnhancedObjectImpl(CtClass clazz) throws NotFoundException, CannotCompileException {
        ClassPool cp = clazz.getClassPool();
        clazz.addInterface(cp.get(EnhancedObject.class.getName()));
        this.writeEnhancedOBjectFields(clazz);
        this.writeEnhancedObjectMethods(clazz);
    }

    private void writeEnhancedOBjectFields(CtClass clazz) throws CannotCompileException, NotFoundException {
        ClassPool cp = clazz.getClassPool();
        CtField cbField = new CtField(cp.get(Map.class.getName()), FIELD_NAME_CALLBACKS, clazz);
        cbField.setModifiers(2);
        clazz.addField(cbField, CtField.Initializer.byExpr((String)"null;"));
        CtField cblField = new CtField(cp.get(ReentrantReadWriteLock.class.getName()), FIELD_NAME_CALLBACKS_LOCK, clazz);
        cblField.setModifiers(2);
        clazz.addField(cblField, CtField.Initializer.byExpr((String)("new " + ReentrantReadWriteLock.class.getName() + "();")));
    }

    private void writeEnhancedObjectMethods(CtClass clazz) throws NotFoundException, CannotCompileException {
        ClassPool cp = clazz.getClassPool();
        CtClass callbackClass = cp.get(Callback.class.getName());
        CtClass mapClass = cp.get(Map.class.getName());
        CtClass reentrantReadWriteLockClass = cp.get(ReentrantReadWriteLock.class.getName());
        CtMethod method = new CtMethod(CtClass.voidType, "addCallback", new CtClass[]{callbackClass}, clazz);
        method.setModifiers(1);
        method.setBody("com.aionemu.commons.callbacks.util.ObjectCallbackHelper.addCallback($1, this);");
        clazz.addMethod(method);
        method = new CtMethod(CtClass.voidType, "removeCallback", new CtClass[]{callbackClass}, clazz);
        method.setModifiers(1);
        method.setBody("com.aionemu.commons.callbacks.util.ObjectCallbackHelper.removeCallback($1, this);");
        clazz.addMethod(method);
        method = new CtMethod(mapClass, "getCallbacks", new CtClass[0], clazz);
        method.setModifiers(1);
        method.setBody("return $$$callbacks;");
        clazz.addMethod(method);
        method = new CtMethod(CtClass.voidType, "setCallbacks", new CtClass[]{mapClass}, clazz);
        method.setModifiers(1);
        method.setBody("this.$$$callbacks = $1;");
        clazz.addMethod(method);
        method = new CtMethod(reentrantReadWriteLockClass, "getCallbackLock", new CtClass[0], clazz);
        method.setModifiers(1);
        method.setBody("return $$$callbackLock;");
        clazz.addMethod(method);
    }

    protected boolean isEnhanceable(CtMethod method) {
        int modifiers = method.getModifiers();
        return !Modifier.isAbstract((int)modifiers) && !Modifier.isNative((int)modifiers) && !Modifier.isStatic((int)modifiers) && CallbacksUtil.isAnnotationPresent(method, ObjectCallback.class);
    }
}

