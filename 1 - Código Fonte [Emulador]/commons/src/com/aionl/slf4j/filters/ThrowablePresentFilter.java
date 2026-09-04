package com.aionl.slf4j.filters;

import ch.qos.logback.classic.spi.ILoggingEvent;
import ch.qos.logback.core.filter.Filter;
import ch.qos.logback.core.spi.FilterReply;

public class ThrowablePresentFilter extends Filter<ILoggingEvent> {
    @Override
    public FilterReply decide(ILoggingEvent loggingEvent) {
        if (loggingEvent.getThrowableProxy() != null) {
            return FilterReply.ACCEPT;
        }
        return FilterReply.DENY;
    }
}
