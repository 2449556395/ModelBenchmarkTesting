package com.example.benchmark;
import java.time.Clock;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicReference;
public class TokenCacheConcurrency {
  private final Clock clock; private final TokenSupplier supplier; private final AtomicReference<Token> cached = new AtomicReference<Token>();
  public TokenCacheConcurrency(Clock clock, TokenSupplier supplier) { this.clock = clock; this.supplier = supplier; }
  public String getToken() { Token token = cached.get(); if (token != null && token.expiresAt.isAfter(clock.instant())) return token.value; synchronized (this) { token = cached.get(); if (token == null || !token.expiresAt.isAfter(clock.instant())) { token = supplier.refresh(); cached.set(token); } return token.value; } }
  public interface TokenSupplier { Token refresh(); }
  public static class Token { public final String value; public final Instant expiresAt; public Token(String value, Instant expiresAt) { this.value = value; this.expiresAt = expiresAt; } }
}
