package com.dawai.controller;

import com.dawai.security.UserContext;
import com.dawai.service.RunService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.Map;

@RestController
@RequestMapping("/api")
public class UploadController {

    private final RunService runService;

    public UploadController(RunService runService) {
        this.runService = runService;
    }

    /**
     * Upload files and run the full pipeline.
     * Matches Python: POST /api/upload + POST /api/run combined.
     */
    @PostMapping("/upload")
    public ResponseEntity<Map<String, Object>> upload(
            @RequestParam("ordered_files") MultipartFile[] orderedFiles,
            @RequestParam("sold_file") MultipartFile soldFile,
            @RequestParam(value = "mapping_file", required = false) MultipartFile mappingFile,
            @RequestParam(value = "date_from", required = false) String dateFrom,
            @RequestParam(value = "date_to", required = false) String dateTo,
            @RequestParam(value = "report_name", required = false) String reportName
    ) {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) {
            return ResponseEntity.status(401).build();
        }
        if (orderedFiles == null || orderedFiles.length == 0) {
            return ResponseEntity.badRequest().body(Map.of("detail", "No supplier files provided"));
        }
        if (soldFile == null || soldFile.isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of("detail", "No inventory report file provided"));
        }
        try {
            Map<String, Object> result = runService.uploadAndRun(
                    orderedFiles, soldFile, mappingFile, userId,
                    dateFrom, dateTo, reportName);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            return ResponseEntity.status(500).body(Map.of("detail",
                    e.getMessage() != null ? e.getMessage() : "Report generation failed"));
        }
    }
}
