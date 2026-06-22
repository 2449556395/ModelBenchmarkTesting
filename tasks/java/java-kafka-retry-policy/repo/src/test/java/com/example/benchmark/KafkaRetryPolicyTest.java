package com.example.benchmark;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class KafkaRetryPolicyTest {
  @Test void retriesTransientErrorsUntilLimit() { KafkaRetryPolicy policy = new KafkaRetryPolicy(3, 100); assertTrue(policy.shouldRetry(1, new RuntimeException("temporary"))); assertFalse(policy.shouldRetry(3, new RuntimeException("temporary"))); }
  @Test void doesNotRetryNonRetryableErrors() { assertFalse(new KafkaRetryPolicy(3, 100).shouldRetry(1, new KafkaRetryPolicy.NonRetryableMessageException("bad payload"))); }
  @Test void usesCappedBackoff() { assertEquals(30000L, new KafkaRetryPolicy(20, 1000).delayMillis(20)); }
}
