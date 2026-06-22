package com.example.benchmark;
import org.junit.jupiter.api.Test;
import java.nio.file.Paths;
import static org.junit.jupiter.api.Assertions.*;
class PathTraversalSecurityTest {
  @Test void resolvesSafePath() { assertTrue(new PathTraversalSecurity(Paths.get("/tmp/base")).resolve("docs/a.txt").toString().endsWith("docs/a.txt")); }
  @Test void rejectsTraversal() { assertThrows(SecurityException.class, () -> new PathTraversalSecurity(Paths.get("/tmp/base")).resolve("../secret.txt")); }
}
