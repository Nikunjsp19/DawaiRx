package com.dawai.controller;

import com.dawai.document.RunDocument;
import com.dawai.security.UserContext;
import com.dawai.service.RunService;
import com.opencsv.exceptions.CsvException;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.nio.file.Path;
import java.util.*;

@RestController
@RequestMapping("/api")
public class RunController {

    private final RunService runService;

    public RunController(RunService runService) {
        this.runService = runService;
    }

    @GetMapping("/runs")
    public ResponseEntity<Map<String, Object>> listRuns(
            @RequestParam(defaultValue = "10") int limit,
            @RequestParam(defaultValue = "0") int offset
    ) {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) {
            return ResponseEntity.status(401).build();
        }
        List<Map<String, Object>> runs = runService.listRuns(userId, limit, offset);
        long total = runService.countRuns(userId);
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("runs", runs);
        body.put("total", total);
        body.put("limit", limit);
        body.put("offset", offset);
        return ResponseEntity.ok(body);
    }

    @GetMapping("/runs/{runId}")
    public ResponseEntity<Map<String, Object>> getRun(@PathVariable String runId) {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) return ResponseEntity.status(401).build();
        Optional<RunDocument> runOpt = runService.getRun(userId, runId);
        if (runOpt.isEmpty()) {
            return ResponseEntity.status(404).body(Map.of("detail", "Run not found"));
        }
        RunDocument run = runOpt.get();
        Map<String, Object> runMap = new LinkedHashMap<>();
        runMap.put("run_id", run.getRunId());
        runMap.put("user_id", run.getUserId());
        runMap.put("created_at", run.getCreatedAt() != null ? run.getCreatedAt().toInstant().toString() : null);
        runMap.put("config_summary", run.getConfigSummary() != null ? run.getConfigSummary() : Map.of());
        runMap.put("stats", run.getStats() != null ? run.getStats() : Map.of());
        runMap.put("input_metadata", run.getInputMetadata() != null ? run.getInputMetadata() : Map.of());

        List<Map<String, Object>> dawairxReport = Collections.emptyList();
        List<String> dawairxColumns = Collections.emptyList();
        int dawairxRowCount = 0;
        boolean isNoData = true;
        String dawairxError = null;
        try {
            dawairxReport = runService.loadReportCsv(runId);
            if (!dawairxReport.isEmpty()) {
                dawairxColumns = new ArrayList<>(dawairxReport.get(0).keySet());
                dawairxRowCount = dawairxReport.size();
                isNoData = false;
            } else {
                dawairxError = "No data available for this report.";
            }
        } catch (IOException | CsvException e) {
            dawairxError = "No data available for this report.";
        }

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("run", runMap);
        response.put("dawairx_report", dawairxReport);
        response.put("dawairx_columns", dawairxColumns);
        response.put("dawairx_row_count", dawairxRowCount);
        response.put("is_no_data", isNoData);
        response.put("dawairx_error", dawairxError);
        return ResponseEntity.ok(response);
    }

    @DeleteMapping("/runs/{runId}")
    public ResponseEntity<Map<String, Object>> deleteRun(@PathVariable String runId) {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) return ResponseEntity.status(401).build();
        boolean deleted = runService.deleteRun(userId, runId);
        if (!deleted) {
            return ResponseEntity.status(404).body(Map.of("detail", "Run not found or you don't have permission to delete it"));
        }
        return ResponseEntity.ok(Map.of("success", true, "message", "Run " + runId + " deleted successfully"));
    }

    /**
     * Download a report artifact.
     * Matches Python: GET /api/download/{run_id}/{file_type}
     * File types: inventory_report, audit_report, audit_report_pdf, audit_report_detailed, summary
     */
    @GetMapping("/download/{runId}/{fileType}")
    public ResponseEntity<Resource> download(
            @PathVariable String runId,
            @PathVariable String fileType
    ) {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) return ResponseEntity.status(401).build();
        Optional<RunDocument> runOpt = runService.getRun(userId, runId);
        if (runOpt.isEmpty()) {
            return ResponseEntity.notFound().build();
        }

        // Map file type to actual filename (matching Python convention)
        String filename;
        String contentType;
        switch (fileType) {
            case "inventory_report" -> { filename = "inventory_report.csv"; contentType = "text/csv"; }
            case "audit_report" -> { filename = "audit_report.xlsx"; contentType = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"; }
            case "audit_report_pdf", "audit_report_detailed" -> { filename = "audit_report_detailed.pdf"; contentType = "application/pdf"; }
            case "summary" -> { filename = "summary.json"; contentType = "application/json"; }
            default -> { filename = fileType; contentType = "application/octet-stream"; }
        }

        Optional<Path> fileOpt = runService.getDownloadFile(runId, filename);
        if (fileOpt.isEmpty()) {
            return ResponseEntity.notFound().build();
        }
        try {
            Path path = fileOpt.get();
            Resource resource = new UrlResource(path.toUri());
            // Use report_name from config for download filename if available
            String downloadName = filename;
            RunDocument run = runOpt.get();
            if (run.getConfigSummary() != null) {
                Object rn = run.getConfigSummary().get("report_name");
                if (rn != null && !rn.toString().isBlank()) {
                    String safe = rn.toString().replaceAll("[^a-zA-Z0-9._-]", "_");
                    String ext = filename.substring(filename.lastIndexOf('.'));
                    downloadName = safe + ext;
                }
            }
            return ResponseEntity.ok()
                    .contentType(MediaType.parseMediaType(contentType))
                    .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + downloadName + "\"")
                    .body(resource);
        } catch (Exception e) {
            return ResponseEntity.notFound().build();
        }
    }

    @GetMapping("/runs/{runId}/medicine/{medicineIdentifier}")
    public ResponseEntity<Map<String, Object>> getMedicine(
            @PathVariable String runId,
            @PathVariable String medicineIdentifier
    ) {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) return ResponseEntity.status(401).build();
        Map<String, Object> detail = runService.getMedicineDetail(userId, runId, medicineIdentifier);
        if (detail == null) {
            return ResponseEntity.status(404).body(Map.of("detail", "Medicine not found: " + medicineIdentifier));
        }
        return ResponseEntity.ok(detail);
    }
}
