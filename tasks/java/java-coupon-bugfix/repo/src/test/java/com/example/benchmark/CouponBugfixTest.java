package com.example.benchmark;
import org.junit.jupiter.api.Test;
import java.math.BigDecimal;
import static org.junit.jupiter.api.Assertions.*;
class CouponBugfixTest {
  private final CouponBugfix service = new CouponBugfix();
  @Test void capsDiscountAtSubtotal() { assertEquals(new BigDecimal("0.00"), service.finalAmount(new BigDecimal("10.00"), new BigDecimal("2.00"), new BigDecimal("100.00"))); }
  @Test void honorsMaxDiscount() { assertEquals(new BigDecimal("80.00"), service.finalAmount(new BigDecimal("100.00"), new BigDecimal("0.50"), new BigDecimal("20.00"))); }
  @Test void rejectsNegativeInput() { assertThrows(IllegalArgumentException.class, () -> service.finalAmount(new BigDecimal("-1"), BigDecimal.ONE, BigDecimal.ONE)); }
}
