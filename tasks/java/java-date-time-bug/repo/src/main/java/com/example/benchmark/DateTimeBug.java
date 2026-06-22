package com.example.benchmark;
import java.time.*;
import java.time.format.DateTimeFormatter;
public class DateTimeBug {
  public String billingDay(Instant instant, ZoneId zone) {
    if (instant == null || zone == null) throw new IllegalArgumentException("instant and zone are required");
    return DateTimeFormatter.ISO_LOCAL_DATE.format(instant.atZone(zone).toLocalDate());
  }
  public boolean isExpired(Instant expiresAt, Clock clock) {
    if (expiresAt == null || clock == null) throw new IllegalArgumentException("expiresAt and clock are required");
    return !expiresAt.isAfter(clock.instant());
  }
}
