package com.example.benchmark;
import org.junit.jupiter.api.Test;
import java.math.BigDecimal;
import java.util.Collections;
import static org.junit.jupiter.api.Assertions.*;
class InvoiceJunitTestsTest {
  @Test void calculatesInvoiceTotal() { assertEquals(new BigDecimal("17.00"), new InvoiceJunitTests().total(InvoiceJunitTests.sample())); }
  @Test void supportsEmptyInvoices() { assertEquals(BigDecimal.ZERO, new InvoiceJunitTests().total(Collections.emptyList())); }
  @Test void rejectsInvalidQuantity() { assertThrows(IllegalArgumentException.class, () -> new InvoiceJunitTests().total(Collections.singletonList(new InvoiceJunitTests.LineItem("X", 0, BigDecimal.ONE)))); }
}
