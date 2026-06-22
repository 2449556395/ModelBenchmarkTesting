package com.example.benchmark;
import org.junit.jupiter.api.Test;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import static org.junit.jupiter.api.Assertions.*;
class UserRepositoryNTest {
  @Test void fetchesOrdersInOneBatch() { AtomicInteger calls = new AtomicInteger(); UserRepositoryN repo = new UserRepositoryN(); List<UserRepositoryN.User> users = Arrays.asList(new UserRepositoryN.User("u1"), new UserRepositoryN.User("u2")); List<UserRepositoryN.UserWithOrders> out = repo.attachOrders(users, ids -> { calls.incrementAndGet(); Map<String, List<UserRepositoryN.Order>> m = new HashMap<String, List<UserRepositoryN.Order>>(); m.put("u1", Collections.singletonList(new UserRepositoryN.Order("o1"))); return m; }); assertEquals(1, calls.get()); assertEquals(1, out.get(0).orders.size()); assertTrue(out.get(1).orders.isEmpty()); }
}
