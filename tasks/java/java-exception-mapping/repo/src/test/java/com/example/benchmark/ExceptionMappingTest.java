package com.example.benchmark;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class ExceptionMappingTest {
  @Test void mapsKnownExceptions() { ExceptionMapping mapper = new ExceptionMapping(); assertEquals(404, mapper.map(new ExceptionMapping.NotFoundException("missing")).status); assertEquals("VALIDATION_ERROR", mapper.map(new ExceptionMapping.ValidationException("bad")).code); }
  @Test void hidesInternalExceptionMessage() { ExceptionMapping.ApiError error = new ExceptionMapping().map(new IllegalStateException("secret")); assertEquals(500, error.status); assertFalse(error.message.contains("secret")); }
}
