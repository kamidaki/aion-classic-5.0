package com.aionl.slf4j.filters;

import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.filter.Filter;
import ch.qos.logback.core.spi.FilterReply;

public class DropFilter
extends Filter<ILoggingEvent> {
    public FilterReply decide(ILoggingEvent loggingEvent) {
        String message = loggingEvent.getMessage();
        if (message.startsWith("[DROP]")) {
            return FilterReply.ACCEPT;
        }
        return FilterReply.DENY;
    }
}

