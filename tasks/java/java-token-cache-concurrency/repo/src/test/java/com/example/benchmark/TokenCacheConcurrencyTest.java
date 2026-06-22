package com.example.benchmark;
import org.junit.jupiter.api.Test;
import java.time.*;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.jupiter.api.Assertions.*;
class TokenCacheConcurrencyTest {
  @Test void reusesNonExpiredToken() { AtomicInteger calls = new AtomicInteger(); Clock clock = Clock.fixed(Instant.parse("2024-01-01T00:00:00Z"), ZoneOffset.UTC); TokenCacheConcurrency cache = new TokenCacheConcurrency(clock, () -> new TokenCacheConcurrency.Token("t" + calls.incrementAndGet(), Instant.parse("2024-01-01T01:00:00Z"))); assertEquals("t1", cache.getToken()); assertEquals("t1", cache.getToken()); assertEquals(1, calls.get()); }
}
