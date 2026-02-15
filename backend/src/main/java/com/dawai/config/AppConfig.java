package com.dawai.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.nio.file.Path;
import java.nio.file.Paths;

@Configuration
public class AppConfig {

    @Value("${app.upload-dir:/tmp/dawai-rx/uploads}")
    private String uploadDir;

    @Value("${app.output-dir:/tmp/dawai-rx/output}")
    private String outputDir;

    @Bean
    public Path uploadDirPath() {
        Path path = Paths.get(uploadDir);
        path.toFile().mkdirs();
        return path;
    }

    @Bean
    public Path outputDirPath() {
        Path path = Paths.get(outputDir);
        path.toFile().mkdirs();
        return path;
    }
}
