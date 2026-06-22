package com.example.benchmark;
public class KafkaRetryPolicy {
  private final int maxAttempts; private final long baseDelayMillis;
  public KafkaRetryPolicy(int maxAttempts, long baseDelayMillis) { if (maxAttempts < 1 || baseDelayMillis < 1) throw new IllegalArgumentException("invalid retry config"); this.maxAttempts = maxAttempts; this.baseDelayMillis = baseDelayMillis; }
  public boolean shouldRetry(int attempt, Throwable error) { return attempt < maxAttempts && !(error instanceof NonRetryableMessageException); }
  public long delayMillis(int attempt) { if (attempt < 1) throw new IllegalArgumentException("attempt must be positive"); long multiplier = 1L << Math.min(attempt - 1, 10); return Math.min(baseDelayMillis * multiplier, 30000L); }
  public static class NonRetryableMessageException extends RuntimeException { public NonRetryableMessageException(String message) { super(message); } }
}
