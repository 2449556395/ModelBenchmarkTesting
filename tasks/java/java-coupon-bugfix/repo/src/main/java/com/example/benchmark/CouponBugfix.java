package com.example.benchmark;
import java.math.BigDecimal;
import java.math.RoundingMode;
public class CouponBugfix {
  public BigDecimal finalAmount(BigDecimal subtotal, BigDecimal discountRate, BigDecimal maxDiscount) {
    if (subtotal == null || discountRate == null || maxDiscount == null) throw new IllegalArgumentException("amounts must not be null");
    if (subtotal.signum() < 0 || discountRate.signum() < 0 || maxDiscount.signum() < 0) throw new IllegalArgumentException("amounts must not be negative");
    BigDecimal discount = subtotal.multiply(discountRate).setScale(2, RoundingMode.HALF_UP);
    if (discount.compareTo(maxDiscount) > 0) discount = maxDiscount;
    if (discount.compareTo(subtotal) > 0) discount = subtotal;
    return subtotal.subtract(discount).setScale(2, RoundingMode.HALF_UP);
  }
}
