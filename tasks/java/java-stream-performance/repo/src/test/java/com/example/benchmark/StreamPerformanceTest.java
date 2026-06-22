package com.example.benchmark;
import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;
class StreamPerformanceTest {
  @Test void countsOnlyActiveCustomers() { List<StreamPerformance.Customer> customers = Arrays.asList(new StreamPerformance.Customer("1", "EU", true, 1), new StreamPerformance.Customer("2", "EU", false, 99), new StreamPerformance.Customer("3", "US", true, 2)); assertEquals(Integer.valueOf(1), new StreamPerformance().countByRegion(customers).get("EU")); }
  @Test void returnsTopCustomersByScore() { List<StreamPerformance.Customer> customers = Arrays.asList(new StreamPerformance.Customer("a", "EU", true, 10), new StreamPerformance.Customer("b", "EU", true, 50)); assertEquals(Collections.singletonList("b"), new StreamPerformance().topCustomerIds(customers, 1)); }
}
