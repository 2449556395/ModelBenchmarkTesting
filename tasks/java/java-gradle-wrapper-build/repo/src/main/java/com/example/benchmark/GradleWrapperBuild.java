package com.example.benchmark;
import java.util.Arrays;
import java.util.List;
public class GradleWrapperBuild {
  public List<String> requiredWrapperFiles() { return Arrays.asList("gradlew", "gradlew.bat", "gradle/wrapper/gradle-wrapper.properties", "gradle/wrapper/gradle-wrapper.jar"); }
  public boolean isSafeTask(String taskName) { return taskName != null && taskName.matches("[A-Za-z][A-Za-z0-9:_-]*") && !taskName.contains(".."); }
}
