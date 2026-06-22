package com.example.benchmark;
import java.time.LocalDate;
import java.util.*;
public class SpringOrderFilter {
  public List<Order> filter(List<Order> orders, String status, LocalDate createdAfter) { List<Order> out = new ArrayList<Order>(); for (Order order : orders) { if (status != null && !status.equals(order.status)) continue; if (createdAfter != null && !order.createdAt.isAfter(createdAfter)) continue; out.add(order); } return out; }
  public static class Order { public final String id; public final String status; public final LocalDate createdAt; public Order(String id, String status, LocalDate createdAt) { this.id = id; this.status = status; this.createdAt = createdAt; } }
}
