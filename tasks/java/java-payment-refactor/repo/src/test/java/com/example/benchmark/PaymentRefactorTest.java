package com.example.benchmark;
import org.junit.jupiter.api.Test;
import java.math.BigDecimal;
import static org.junit.jupiter.api.Assertions.*;
class PaymentRefactorTest {
  @Test void chargesCardFee() { assertEquals(new BigDecimal("2.90"), new PaymentRefactor().charge(new PaymentRefactor.PaymentRequest(PaymentRefactor.Method.CARD, new BigDecimal("100.00"))).fee); }
  @Test void bankTransferHasNoFee() { assertEquals(BigDecimal.ZERO, new PaymentRefactor().charge(new PaymentRefactor.PaymentRequest(PaymentRefactor.Method.BANK_TRANSFER, new BigDecimal("100.00"))).fee); }
}
