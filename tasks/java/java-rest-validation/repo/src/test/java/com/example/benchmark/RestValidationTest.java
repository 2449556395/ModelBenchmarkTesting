package com.example.benchmark;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class RestValidationTest {
  @Test void acceptsValidRequest() { RestValidation.CreateUserRequest r = new RestValidation.CreateUserRequest(); r.email = "a@example.com"; r.name = "Ada"; r.age = 18; assertTrue(new RestValidation().validate(r).isEmpty()); }
  @Test void returnsAllValidationErrors() { RestValidation.CreateUserRequest r = new RestValidation.CreateUserRequest(); r.email = "bad"; r.name = " "; r.age = 10; assertEquals(3, new RestValidation().validate(r).size()); }
}
