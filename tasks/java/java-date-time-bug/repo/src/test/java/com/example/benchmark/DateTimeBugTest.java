package com.example.benchmark;
import org.junit.jupiter.api.Test;
import java.time.*;
import static org.junit.jupiter.api.Assertions.*;
class DateTimeBugTest {
  private final DateTimeBug service = new DateTimeBug();
  @Test void convertsUsingProvidedZone() { assertEquals("2024-02-29", service.billingDay(Instant.parse("2024-03-01T00:30:00Z"), ZoneId.of("America/Los_Angeles"))); }
  @Test void treatsEqualInstantAsExpired() { Instant now = Instant.parse("2024-01-01T00:00:00Z"); assertTrue(service.isExpired(now, Clock.fixed(now, ZoneOffset.UTC))); }
}
