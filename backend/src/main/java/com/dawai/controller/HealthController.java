package com.dawai.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class HealthController {

    @GetMapping("/")
    public ResponseEntity<Map<String, String>> root() {
        return ResponseEntity.ok(Map.of("status", "ok"));
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> health() {
        return ResponseEntity.ok(Map.of("status", "ok"));
    }

    // Azure warm-up/health probes sometimes hit this path.
    @GetMapping("/robots933456.txt")
    public ResponseEntity<Map<String, String>> probe() {
        return ResponseEntity.ok(Map.of("status", "ok"));
    }
}
