package com.example.benchmark;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class GradleWrapperBuildTest {
  @Test void validatesSafeGradleTaskNames() { GradleWrapperBuild build = new GradleWrapperBuild(); assertTrue(build.isSafeTask("cleanTest")); assertFalse(build.isSafeTask("../clean")); }
  @Test void documentsWrapperFiles() { assertTrue(new GradleWrapperBuild().requiredWrapperFiles().contains("gradlew")); }
}
