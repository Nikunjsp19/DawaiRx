package com.dawai.reporting;

import com.dawai.ingestion.ColumnMapper;
import com.dawai.ingestion.FileLoader;
import com.dawai.normalization.NormalizationService;
import com.dawai.reconciliation.ReconciliationService;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Integration test: ingest fixture CSVs → normalize → reconcile → DawaiRx report.
 * Validates column names, ranking, amount/cost, zero→blank behavior.
 */
class DawairxReportBuilderTest {

    @TempDir
    Path tempDir;

    private final FileLoader fileLoader = new FileLoader();
    private final ColumnMapper columnMapper = new ColumnMapper();
    private final NormalizationService normSvc = new NormalizationService();
    private final ReconciliationService reconSvc = new ReconciliationService();

    @Test
    void fullPipeline_fixtureFiles() throws Exception {
        // Load fixture files
        Path orderedSmith = Path.of(getClass().getClassLoader().getResource("fixtures/ordered_smith.csv").toURI());
        Path orderedKinray = Path.of(getClass().getClassLoader().getResource("fixtures/ordered_kinray.csv").toURI());
        Path soldFile = Path.of(getClass().getClassLoader().getResource("fixtures/sold_report.csv").toURI());

        // --- Ingest ordered files ---
        List<Map<String, Object>> allOrdered = new ArrayList<>();
        List<String> supplierNames = new ArrayList<>();
        for (var entry : List.of(Map.entry(orderedSmith, "SMITH DRUGS"), Map.entry(orderedKinray, "KINRAY"))) {
            List<Map<String, String>> rows = fileLoader.loadFile(entry.getKey());
            Map<String, String> mapping = columnMapper.createMapping(rows.get(0).keySet(), "ordered");
            rows = columnMapper.applyMapping(rows, mapping);
            for (Map<String, String> row : rows) row.put("supplier_name", entry.getValue());
            supplierNames.add(entry.getValue());
            List<Map<String, Object>> normalized = normSvc.normalize(rows, "ordered");
            allOrdered.addAll(normalized);
        }

        // --- Ingest sold file ---
        List<Map<String, String>> soldRaw = fileLoader.loadFile(soldFile);
        Map<String, String> soldMapping = columnMapper.createMapping(soldRaw.get(0).keySet(), "sold");
        soldRaw = columnMapper.applyMapping(soldRaw, soldMapping);
        List<Map<String, Object>> allSold = normSvc.normalize(soldRaw, "sold");

        // --- Reconcile ---
        List<Map<String, Object>> reconciled = reconSvc.reconcile(allOrdered, allSold);
        assertFalse(reconciled.isEmpty(), "Reconciliation must produce results");

        // --- Build report ---
        Path outputCsv = tempDir.resolve("inventory_report.csv");
        List<Map<String, Object>> report = DawairxReportBuilder.buildAndWrite(
                outputCsv, reconciled, allSold, allOrdered, supplierNames);

        assertTrue(Files.exists(outputCsv), "Report CSV must exist");
        assertFalse(report.isEmpty(), "Report must have rows");

        // --- Validate column names ---
        Set<String> cols = report.get(0).keySet();
        assertTrue(cols.contains("NDC"), "Must have NDC column");
        assertTrue(cols.contains("DRUG NAME"), "Must have DRUG NAME column");
        assertTrue(cols.contains("RANK"), "Must have RANK column");
        assertTrue(cols.contains("PKG SIZE"), "Must have PKG SIZE column");
        assertTrue(cols.contains("TOTAL\nORDERED-O"), "Must have TOTAL\\nORDERED-O column");
        assertTrue(cols.contains("TOTAL\nBILLED-B"), "Must have TOTAL\\nBILLED-B column");
        assertTrue(cols.contains("TOTAL\nSHORTAGE-S"), "Must have TOTAL\\nSHORTAGE-S column");
        assertTrue(cols.contains("HIGHEST\nSHORTAGE-S"), "Must have HIGHEST\\nSHORTAGE-S column");
        assertTrue(cols.contains("AMOUNT"), "Must have AMOUNT column");
        assertTrue(cols.contains("COST"), "Must have COST column");
        assertTrue(cols.contains("medicine_key"), "Must have medicine_key column");

        // --- Validate only medicines with sales appear (Atorvastatin has 0 sold) ---
        List<String> drugNames = report.stream()
                .map(r -> String.valueOf(r.get("DRUG NAME")).toUpperCase(Locale.ROOT))
                .collect(Collectors.toList());
        // Atorvastatin was only ordered, never sold → should NOT appear
        boolean hasAtorvastatin = drugNames.stream()
                .anyMatch(d -> d.contains("ATORVASTATIN"));
        assertFalse(hasAtorvastatin, "Atorvastatin (not sold) must be filtered out");

        // --- Validate RANK is consecutive ---
        for (int i = 0; i < report.size(); i++) {
            String rank = String.valueOf(report.get(i).get("RANK"));
            assertEquals(String.valueOf(i + 1), rank, "RANK must be consecutive starting at 1");
        }

        // --- Validate AMOUNT uses floor (check Aspirin: 45.50 + 92.75 = 138.25 → floor = 138) ---
        Map<String, Object> aspirinRow = report.stream()
                .filter(r -> {
                    String key = String.valueOf(r.get("medicine_key"));
                    return key.contains("12345678901");
                })
                .findFirst().orElse(null);
        assertNotNull(aspirinRow, "Aspirin must appear in report");
        String aspirinAmount = String.valueOf(aspirinRow.get("AMOUNT"));
        assertEquals("138", aspirinAmount, "AMOUNT must use floor(45.50+92.75) = 138");

        // --- Validate zero values show as blank ---
        for (Map<String, Object> row : report) {
            Object highest = row.get("HIGHEST\nSHORTAGE-S");
            // HIGHEST SHORTAGE-S should be blank (empty string) for positive/zero shortage
            // and have a value for negative shortage (leftover)
            if (highest != null && !highest.toString().isEmpty()) {
                double val = Double.parseDouble(highest.toString());
                assertTrue(val < 0, "HIGHEST SHORTAGE-S should only have negative values");
            }
        }

        // --- Validate insurance columns exist ---
        boolean hasBlueCross = cols.stream().anyMatch(c -> c.contains("BlueCross"));
        boolean hasAetna = cols.stream().anyMatch(c -> c.contains("Aetna"));
        assertTrue(hasBlueCross, "BlueCross insurance column must exist");
        assertTrue(hasAetna, "Aetna insurance column must exist");

        // --- Validate supplier columns exist ---
        boolean hasSmith = cols.stream().anyMatch(c -> c.contains("SMITH DRUGS"));
        boolean hasKinray = cols.stream().anyMatch(c -> c.contains("KINRAY"));
        assertTrue(hasSmith, "SMITH DRUGS supplier column must exist");
        assertTrue(hasKinray, "KINRAY supplier column must exist");
    }

    @Test
    void emptyReconciled_writesHeaderOnly() throws Exception {
        Path outputCsv = tempDir.resolve("empty_report.csv");
        List<Map<String, Object>> result = DawairxReportBuilder.buildAndWrite(
                outputCsv, Collections.emptyList(), Collections.emptyList(),
                Collections.emptyList(), Collections.emptyList());
        assertTrue(result.isEmpty());
        assertTrue(Files.exists(outputCsv));
        // Header row may span multiple text lines because column names contain \n
        // (e.g. "TOTAL\nORDERED-O"); just verify file is non-empty and has no data rows
        String content = Files.readString(outputCsv);
        assertTrue(content.contains("NDC"), "Header must include NDC");
        assertTrue(content.contains("DRUG NAME"), "Header must include DRUG NAME");
        // Should NOT have a second CSV record (only header)
        try (var reader = new com.opencsv.CSVReaderBuilder(
                new java.io.InputStreamReader(Files.newInputStream(outputCsv))).build()) {
            var rows = reader.readAll();
            assertEquals(1, rows.size(), "Empty report CSV should have header row only");
        }
    }
}
