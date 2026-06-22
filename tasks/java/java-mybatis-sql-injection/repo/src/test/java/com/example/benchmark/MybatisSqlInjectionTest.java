package com.example.benchmark;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class MybatisSqlInjectionTest {
  @Test void usesBindParameterForStatus() { MybatisSqlInjection.Query q = new MybatisSqlInjection().buildQuery("ACTIVE' OR 1=1 --", "name"); assertTrue(q.sql.contains("status = ?")); assertFalse(q.sql.contains("OR 1=1")); assertEquals("ACTIVE' OR 1=1 --", q.params.get(0)); }
  @Test void whitelistsSortColumn() { assertTrue(new MybatisSqlInjection().buildQuery("ACTIVE", "name desc; drop table users").sql.endsWith("ORDER BY id")); }
}
