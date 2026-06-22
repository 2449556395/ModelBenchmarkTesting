package com.example.benchmark;
import java.util.*;
public class StreamPerformance {
  public Map<String, Integer> countByRegion(List<Customer> customers) { Map<String, Integer> counts = new HashMap<String, Integer>(); for (Customer c : customers) if (c.active) counts.put(c.region, counts.getOrDefault(c.region, 0) + 1); return counts; }
  public List<String> topCustomerIds(List<Customer> customers, int limit) { List<Customer> copy = new ArrayList<Customer>(customers); copy.sort((a, b) -> Integer.compare(b.score, a.score)); List<String> ids = new ArrayList<String>(); for (int i = 0; i < copy.size() && i < limit; i++) ids.add(copy.get(i).id); return ids; }
  public static class Customer { public final String id; public final String region; public final boolean active; public final int score; public Customer(String id, String region, boolean active, int score) { this.id = id; this.region = region; this.active = active; this.score = score; } }
}
