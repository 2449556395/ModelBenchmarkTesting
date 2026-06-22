package com.example.benchmark;
import java.util.*;
public class MybatisSqlInjection {
  private static final Set<String> ALLOWED_SORT = new HashSet<String>(Arrays.asList("id", "name", "created_at"));
  public Query buildQuery(String status, String sortBy) { StringBuilder sql = new StringBuilder("SELECT * FROM users WHERE 1=1"); List<Object> params = new ArrayList<Object>(); if (status != null && !status.trim().isEmpty()) { sql.append(" AND status = ?"); params.add(status.trim()); } String safeSort = ALLOWED_SORT.contains(sortBy) ? sortBy : "id"; sql.append(" ORDER BY ").append(safeSort); return new Query(sql.toString(), params); }
  public static class Query { public final String sql; public final List<Object> params; Query(String sql, List<Object> params) { this.sql = sql; this.params = params; } }
}
