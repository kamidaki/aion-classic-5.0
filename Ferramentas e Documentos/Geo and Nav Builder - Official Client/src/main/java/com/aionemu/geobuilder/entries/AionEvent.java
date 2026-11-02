package com.aionemu.geobuilder.entries;

public enum AionEvent {
  NONE(0, "none"),
  CHRISTMAS(1, "christmas"),
  HALLOWEEN(2, "halloween"),
  VALENTINE(4, "valentine"),
  OVERSEA_MAID(8, "oversea_maid"),
  EVENT_10(10, "event_10");

  private final int id;
  private final String eventName;

  AionEvent(int id, String eventName) {
    this.id = id;
    this.eventName = eventName;
  }

  public int getId() {
    return id;
  }

  public String getEventName() {
    return eventName;
  }
}
