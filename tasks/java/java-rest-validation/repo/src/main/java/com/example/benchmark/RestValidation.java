package com.example.benchmark;
import java.util.*;
public class RestValidation {
  public List<String> validate(CreateUserRequest request) { List<String> errors = new ArrayList<String>(); if (request == null) { errors.add("request.required"); return errors; } if (blank(request.email) || !request.email.contains("@")) errors.add("email.invalid"); if (blank(request.name) || request.name.trim().length() < 2) errors.add("name.too_short"); if (request.age < 13) errors.add("age.too_young"); return errors; }
  private boolean blank(String value) { return value == null || value.trim().isEmpty(); }
  public static class CreateUserRequest { public String email; public String name; public int age; }
}
