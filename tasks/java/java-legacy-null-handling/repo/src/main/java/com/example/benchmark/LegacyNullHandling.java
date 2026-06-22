package com.example.benchmark;
import java.util.Optional;
public class LegacyNullHandling {
  public String displayName(User user) { return Optional.ofNullable(user).map(u -> firstNonBlank(u.nickname, u.fullName, u.email)).orElse("Anonymous"); }
  private String firstNonBlank(String... values) { for (String value : values) if (value != null && !value.trim().isEmpty()) return value.trim(); return "Anonymous"; }
  public static class User { public String nickname; public String fullName; public String email; }
}
