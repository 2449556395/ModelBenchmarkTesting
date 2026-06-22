package com.example.benchmark;
public class ExceptionMapping {
  public ApiError map(RuntimeException ex) {
    if (ex instanceof NotFoundException) return new ApiError(404, "NOT_FOUND", ex.getMessage());
    if (ex instanceof ValidationException) return new ApiError(400, "VALIDATION_ERROR", ex.getMessage());
    return new ApiError(500, "INTERNAL_ERROR", "Unexpected error");
  }
  public static class ApiError { public final int status; public final String code; public final String message; public ApiError(int status, String code, String message) { this.status = status; this.code = code; this.message = message; } }
  public static class NotFoundException extends RuntimeException { public NotFoundException(String message) { super(message); } }
  public static class ValidationException extends RuntimeException { public ValidationException(String message) { super(message); } }
}
