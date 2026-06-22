package com.example.benchmark;
import java.util.*;
public class UserRepositoryN {
  public List<UserWithOrders> attachOrders(List<User> users, OrderGateway gateway) { Map<String, List<Order>> byUser = gateway.findOrdersForUserIds(ids(users)); List<UserWithOrders> result = new ArrayList<UserWithOrders>(); for (User user : users) result.add(new UserWithOrders(user, byUser.getOrDefault(user.id, Collections.emptyList()))); return result; }
  private List<String> ids(List<User> users) { List<String> ids = new ArrayList<String>(); for (User user : users) ids.add(user.id); return ids; }
  public interface OrderGateway { Map<String, List<Order>> findOrdersForUserIds(List<String> ids); }
  public static class User { public final String id; public User(String id) { this.id = id; } }
  public static class Order { public final String id; public Order(String id) { this.id = id; } }
  public static class UserWithOrders { public final User user; public final List<Order> orders; public UserWithOrders(User user, List<Order> orders) { this.user = user; this.orders = orders; } }
}
