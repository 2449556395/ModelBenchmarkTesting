package com.example.benchmark;
import org.junit.jupiter.api.Test;
import java.util.Properties;
import static org.junit.jupiter.api.Assertions.*;
class MavenBuildFixTest {
  @Test void defaultsToJava8Target() { assertEquals("1.8", new MavenBuildFix().compilerTarget(new Properties())); }
  @Test void detectsSkippedTests() { assertFalse(new MavenBuildFix().testsAreEnabled("-DskipTests")); }
}
