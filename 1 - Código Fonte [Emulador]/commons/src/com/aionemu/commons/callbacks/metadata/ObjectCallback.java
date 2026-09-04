package com.aionemu.commons.callbacks.metadata;

import com.aionemu.commons.callbacks.Callback;
import java.lang.annotation.Documented;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

@Documented
@Target(value={ElementType.METHOD})
@Retention(value=RetentionPolicy.RUNTIME)
public @interface ObjectCallback {
    public Class<? extends Callback> value();
}

