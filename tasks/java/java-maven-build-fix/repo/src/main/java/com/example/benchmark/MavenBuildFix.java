package com.example.benchmark;
import java.util.Properties;
public class MavenBuildFix {
  public String compilerTarget(Properties properties) { return properties.getProperty("maven.compiler.target", properties.getProperty("java.version", "1.8")); }
  public boolean testsAreEnabled(String argLine) { return argLine == null || (!argLine.contains("skipTests") && !argLine.contains("maven.test.skip")); }
}
