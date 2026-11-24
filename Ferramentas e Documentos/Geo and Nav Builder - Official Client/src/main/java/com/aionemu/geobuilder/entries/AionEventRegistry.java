package com.aionemu.geobuilder.entries;

import java.util.HashMap;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

public class AionEventRegistry {
  private static final Logger log = Logger.getLogger("GeoBuilder");
  private static final Map<String, AionEvent> registry = new HashMap<>();

  static {
    for (AionEvent event : AionEvent.values()) {
      registry.put(event.getEventName().toLowerCase(), event);
      registry.put(event.name().toLowerCase(), event);
    }
  }

  public static int resolveEventId(String eventTypeName, EntityEntry entry) {
    if (eventTypeName == null || eventTypeName.trim().isEmpty()) {
      return 0;
    }
    String normalized = eventTypeName.toLowerCase().trim();

    // Check registry
    AionEvent registered = registry.get(normalized);
    if (registered != null) {
      return registered.getId();
    }

    // Dynamic fallback handler
    // If name ends with _<number>, parse that number
    int lastUnderscore = normalized.lastIndexOf('_');
    if (lastUnderscore != -1 && lastUnderscore < normalized.length() - 1) {
      String suffix = normalized.substring(lastUnderscore + 1);
      try {
        int parsedId = Integer.parseInt(suffix);
        if (log.isLoggable(Level.FINE)) {
          log.fine("Dynamic fallback parsed event ID " + parsedId + " from '" + eventTypeName + "'");
        }
        return parsedId;
      } catch (NumberFormatException e) {
        // Fall through
      }
    }

    // Attempt to parse the whole string as integer
    try {
      int parsedId = Integer.parseInt(normalized);
      if (log.isLoggable(Level.FINE)) {
        log.fine("Dynamic fallback parsed event ID " + parsedId + " from integer string '" + eventTypeName + "'");
      }
      return parsedId;
    } catch (NumberFormatException e) {
      // Fall through
    }

    // Unknown event type: Graceful handling without crashing
    if (log.isLoggable(Level.FINE)) {
      log.fine("Unknown event type: '" + eventTypeName + "' for Entity '" + (entry != null ? entry.name : "null") + "'.");
    }
    if (entry != null) {
      entry.rawEventMetadata = eventTypeName;
    }
    return 0; // fallback to 0 safely
  }
}
