package com.example.benchmark;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class LegacyNullHandlingTest {
  @Test void fallsBackAcrossUserFields() { LegacyNullHandling.User user = new LegacyNullHandling.User(); user.nickname = " "; user.fullName = null; user.email = "a@example.com"; assertEquals("a@example.com", new LegacyNullHandling().displayName(user)); }
  @Test void handlesNullUser() { assertEquals("Anonymous", new LegacyNullHandling().displayName(null)); }
}
