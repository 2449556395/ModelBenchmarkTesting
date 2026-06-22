package com.example.benchmark;
import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
public class InvoiceJunitTests {
  public BigDecimal total(List<LineItem> items) {
    if (items == null) throw new IllegalArgumentException("items required");
    BigDecimal total = BigDecimal.ZERO;
    for (LineItem item : items) {
      if (item.quantity <= 0 || item.unitPrice.signum() < 0) throw new IllegalArgumentException("invalid line item");
      total = total.add(item.unitPrice.multiply(BigDecimal.valueOf(item.quantity)));
    }
    return total;
  }
  public static class LineItem { public final String sku; public final int quantity; public final BigDecimal unitPrice; public LineItem(String sku, int quantity, BigDecimal unitPrice) { this.sku = sku; this.quantity = quantity; this.unitPrice = unitPrice; } }
  public static List<LineItem> sample() { List<LineItem> items = new ArrayList<LineItem>(); items.add(new LineItem("A", 2, new BigDecimal("3.50"))); items.add(new LineItem("B", 1, new BigDecimal("10.00"))); return items; }
}
