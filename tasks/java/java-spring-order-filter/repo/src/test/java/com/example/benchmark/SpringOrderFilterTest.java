package com.example.benchmark;
import org.junit.jupiter.api.Test;
import java.time.LocalDate;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
class SpringOrderFilterTest {
  @Test void filtersByStatusAndCreatedAfter() { List<SpringOrderFilter.Order> orders = Arrays.asList(new SpringOrderFilter.Order("1", "PAID", LocalDate.parse("2024-01-01")), new SpringOrderFilter.Order("2", "PAID", LocalDate.parse("2024-02-01")), new SpringOrderFilter.Order("3", "CANCELLED", LocalDate.parse("2024-03-01"))); assertEquals("2", new SpringOrderFilter().filter(orders, "PAID", LocalDate.parse("2024-01-15")).get(0).id); }
}
