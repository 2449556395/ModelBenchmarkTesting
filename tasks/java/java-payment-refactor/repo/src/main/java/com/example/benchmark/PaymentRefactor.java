package com.example.benchmark;
import java.math.BigDecimal;
import java.math.RoundingMode;
public class PaymentRefactor {
  public Receipt charge(PaymentRequest request) { validate(request); BigDecimal fee = feeFor(request.method, request.amount); return new Receipt(request.amount.add(fee), fee, "APPROVED"); }
  private void validate(PaymentRequest request) { if (request == null || request.amount == null || request.amount.signum() <= 0) throw new IllegalArgumentException("invalid request"); if (request.method == null) throw new IllegalArgumentException("method required"); }
  private BigDecimal feeFor(Method method, BigDecimal amount) { switch (method) { case CARD: return amount.multiply(new BigDecimal("0.029")).setScale(2, RoundingMode.HALF_UP); case BANK_TRANSFER: return BigDecimal.ZERO; default: throw new IllegalArgumentException("unsupported method"); } }
  public enum Method { CARD, BANK_TRANSFER }
  public static class PaymentRequest { public final Method method; public final BigDecimal amount; public PaymentRequest(Method method, BigDecimal amount) { this.method = method; this.amount = amount; } }
  public static class Receipt { public final BigDecimal total; public final BigDecimal fee; public final String status; public Receipt(BigDecimal total, BigDecimal fee, String status) { this.total = total; this.fee = fee; this.status = status; } }
}
