package com.dawai.service;

import com.dawai.document.RunDocument;
import com.dawai.document.RunItemDocument;
import com.dawai.document.RunIssueDocument;
import com.dawai.ingestion.ColumnMapper;
import com.dawai.ingestion.FileLoader;
import com.dawai.normalization.NdcNormalizer;
import com.dawai.normalization.NormalizationService;
import com.dawai.reconciliation.ReconciliationService;
import com.dawai.reporting.DawairxReportBuilder;
import com.dawai.reporting.ExcelReportBuilder;
import com.dawai.repository.RunItemRepository;
import com.dawai.repository.RunIssueRepository;
import com.dawai.repository.RunRepository;
import com.dawai.rules.RuleEngine;
import com.opencsv.CSVReader;
import com.opencsv.CSVReaderBuilder;
import com.opencsv.CSVWriter;
import com.opencsv.exceptions.CsvException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.aggregation.*;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDate;
import java.time.format.DateTimeParseException;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * Complete report-generation pipeline matching Python: src/web/app.py POST /api/run.
 *
 * Flow: upload files → ingest → normalize → date-filter → reconcile → rules
 *       → DawaiRx CSV → Excel → source CSVs → MongoDB persistence
 */
@Service
public class RunService {

    private static final Logger log = LoggerFactory.getLogger(RunService.class);
    private static final String RUNS_COLLECTION = "runs";

    private final RunRepository runRepository;
    private final RunItemRepository runItemRepository;
    private final RunIssueRepository runIssueRepository;
    private final Path outputDirPath;
    private final Path uploadDirPath;
    private final String fallbackOutputDir;
    private final MongoTemplate mongoTemplate;
    private final ReconciliationService reconciliationService;
    private final NormalizationService normalizationService;
    private final FileLoader fileLoader;
    private final ColumnMapper columnMapper;
    private final RuleEngine ruleEngine;

    public RunService(RunRepository runRepository,
                      RunItemRepository runItemRepository,
                      RunIssueRepository runIssueRepository,
                      @Qualifier("outputDirPath") Path outputDirPath,
                      @Qualifier("uploadDirPath") Path uploadDirPath,
                      @Value("${app.fallback-output-dir:}") String fallbackOutputDir,
                      MongoTemplate mongoTemplate,
                      ReconciliationService reconciliationService,
                      NormalizationService normalizationService,
                      FileLoader fileLoader,
                      ColumnMapper columnMapper,
                      RuleEngine ruleEngine) {
        this.runRepository = runRepository;
        this.runItemRepository = runItemRepository;
        this.runIssueRepository = runIssueRepository;
        this.outputDirPath = outputDirPath;
        this.uploadDirPath = uploadDirPath;
        this.fallbackOutputDir = fallbackOutputDir != null ? fallbackOutputDir.trim() : "";
        this.mongoTemplate = mongoTemplate;
        this.reconciliationService = reconciliationService;
        this.normalizationService = normalizationService;
        this.fileLoader = fileLoader;
        this.columnMapper = columnMapper;
        this.ruleEngine = ruleEngine;
    }

    // ====================== UPLOAD + RUN PIPELINE ======================

    /**
     * Upload files, run the full pipeline, and return run_id.
     * Matches Python: POST /api/upload + POST /api/run combined.
     */
    public Map<String, Object> uploadAndRun(
            MultipartFile[] orderedFiles,
            MultipartFile soldFile,
            MultipartFile mappingFile,
            String userId,
            String dateFrom,
            String dateTo,
            String reportName
    ) throws IOException {
        String runId = generateRunId();

        Path runUploadDir = uploadDirPath.resolve(runId);
        Path runOutputDir = outputDirPath.resolve(runId);
        Files.createDirectories(runUploadDir);
        Files.createDirectories(runOutputDir);

        // Save uploaded files to disk
        List<Path> orderedPaths = new ArrayList<>();
        if (orderedFiles != null) {
            for (int i = 0; i < orderedFiles.length; i++) {
                MultipartFile f = orderedFiles[i];
                if (f != null && !f.isEmpty()) {
                    String name = "ordered_" + i + "_" + sanitizeFilename(f.getOriginalFilename());
                    Path dest = runUploadDir.resolve(name);
                    f.transferTo(dest.toFile());
                    orderedPaths.add(dest);
                }
            }
        }
        Path soldPath = null;
        if (soldFile != null && !soldFile.isEmpty()) {
            soldPath = runUploadDir.resolve("sold_" + sanitizeFilename(soldFile.getOriginalFilename()));
            soldFile.transferTo(soldPath.toFile());
        }
        if (mappingFile != null && !mappingFile.isEmpty()) {
            Path mp = runUploadDir.resolve("mapping_" + sanitizeFilename(mappingFile.getOriginalFilename()));
            mappingFile.transferTo(mp.toFile());
        }

        // ---- Run the full pipeline ----
        PipelineResult result = runPipeline(runId, orderedPaths, soldPath, runOutputDir, dateFrom, dateTo, reportName, userId);

        // ---- Persist to MongoDB ----
        persistRun(runId, userId, orderedPaths, soldPath, result, dateFrom, dateTo, reportName);

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("run_id", runId);
        response.put("dawairx_report", result.dawairxReport);
        response.put("dawairx_columns", result.dawairxColumns);
        response.put("dawairx_row_count", result.dawairxReport.size());
        response.put("summary", result.summary);
        return response;
    }

    /** Legacy upload method for UploadController backward-compat. */
    public Map<String, Object> uploadFiles(
            MultipartFile[] orderedFiles,
            MultipartFile soldFile,
            MultipartFile mappingFile,
            String userId) throws IOException {
        return uploadAndRun(orderedFiles, soldFile, mappingFile, userId, null, null, null);
    }

    // ====================== PIPELINE CORE ======================

    private PipelineResult runPipeline(
            String runId, List<Path> orderedPaths, Path soldPath,
            Path runOutputDir, String dateFrom, String dateTo,
            String reportName, String userId) throws IOException {

        log.info("Pipeline start for run {} ({} ordered files)", runId, orderedPaths.size());

        // --- 1. Ingest: load files and apply column mapping ---
        List<Map<String, String>> allOrderedRaw = new ArrayList<>();
        List<String> allSupplierNames = new ArrayList<>();
        for (Path p : orderedPaths) {
            List<Map<String, String>> rows = fileLoader.loadFile(p);
            Map<String, String> mapping = columnMapper.createMapping(
                    rows.isEmpty() ? Collections.emptySet() : rows.get(0).keySet(), "ordered");
            rows = columnMapper.applyMapping(rows, mapping);

            // Extract supplier name from filename
            String supplier = extractSupplierName(p.getFileName().toString());
            for (Map<String, String> row : rows) {
                row.put("supplier_name", supplier);
            }
            allSupplierNames.add(supplier);
            allOrderedRaw.addAll(rows);
        }

        List<Map<String, String>> soldRaw = Collections.emptyList();
        if (soldPath != null) {
            soldRaw = fileLoader.loadFile(soldPath);
            Map<String, String> mapping = columnMapper.createMapping(
                    soldRaw.isEmpty() ? Collections.emptySet() : soldRaw.get(0).keySet(), "sold");
            soldRaw = columnMapper.applyMapping(soldRaw, mapping);
        }

        // --- 2. Normalize ---
        List<Map<String, Object>> orderedNormalized = normalizationService.normalize(allOrderedRaw, "ordered");
        List<Map<String, Object>> soldNormalized = normalizationService.normalize(soldRaw, "sold");
        log.info("  Normalized: {} ordered rows, {} sold rows", orderedNormalized.size(), soldNormalized.size());

        // --- 3. Date filtering ---
        if (dateFrom != null || dateTo != null) {
            LocalDate from = parseIsoDate(dateFrom);
            LocalDate to = parseIsoDate(dateTo);
            orderedNormalized = filterByDate(orderedNormalized,
                    List.of("order_date", "invoice_date", "purchase_date", "claim_date", "date_filled", "fill_date"), from, to);
            soldNormalized = filterByDate(soldNormalized,
                    List.of("claim_date", "date_filled", "fill_date", "dispense_date"), from, to);
            log.info("  After date filter: {} ordered, {} sold", orderedNormalized.size(), soldNormalized.size());
        }

        // --- 4. Reconcile ---
        List<Map<String, Object>> reconciled = reconciliationService.reconcile(orderedNormalized, soldNormalized);
        Map<String, Object> summary = reconciliationService.generateSummary(reconciled);
        log.info("  Reconciled: {} medicines", reconciled.size());

        // --- 5. Rules ---
        List<Map<String, Object>> issues = ruleEngine.runAll(orderedNormalized, soldNormalized, reconciled);
        summary.put("total_issues", issues.size());

        // --- 6. Save source CSVs (for medicine detail) ---
        writeSourceCsv(runOutputDir.resolve("source_ordered.csv"), orderedNormalized);
        writeSourceCsv(runOutputDir.resolve("source_sold.csv"), soldNormalized);

        // --- 7. DawaiRx report ---
        Path reportCsv = runOutputDir.resolve("inventory_report.csv");
        List<Map<String, Object>> dawairxReport = DawairxReportBuilder.buildAndWrite(
                reportCsv, reconciled, soldNormalized, orderedNormalized, allSupplierNames);
        List<String> dawairxColumns = dawairxReport.isEmpty() ? Collections.emptyList()
                : new ArrayList<>(dawairxReport.get(0).keySet());
        log.info("  DawaiRx report: {} rows, {} columns", dawairxReport.size(), dawairxColumns.size());

        // --- 8. Excel report ---
        try {
            ExcelReportBuilder.write(
                    runOutputDir.resolve("audit_report.xlsx"),
                    dawairxReport, dawairxColumns, summary, issues);
        } catch (Exception e) {
            log.warn("Excel report generation failed: {}", e.getMessage());
        }

        // --- 9. Summary JSON ---
        writeSummaryJson(runOutputDir.resolve("summary.json"), summary, reportName, dateFrom, dateTo);

        PipelineResult result = new PipelineResult();
        result.reconciled = reconciled;
        result.summary = summary;
        result.issues = issues;
        result.dawairxReport = dawairxReport;
        result.dawairxColumns = dawairxColumns;
        return result;
    }

    // ====================== PERSISTENCE ======================

    private void persistRun(String runId, String userId, List<Path> orderedPaths,
                            Path soldPath, PipelineResult result,
                            String dateFrom, String dateTo, String reportName) {
        // --- Run document ---
        RunDocument run = new RunDocument();
        run.setRunId(runId);
        run.setUserId(userId);
        run.setCreatedAt(new Date());
        run.setStats(result.summary);

        Map<String, Object> config = new LinkedHashMap<>();
        config.put("source", "upload");
        config.put("mapping_used", false);
        if (dateFrom != null) config.put("date_from", dateFrom);
        if (dateTo != null) config.put("date_to", dateTo);
        if (reportName != null) config.put("report_name", reportName);
        run.setConfigSummary(config);

        Map<String, Object> inputMeta = new LinkedHashMap<>();
        if (!orderedPaths.isEmpty()) {
            inputMeta.put("ordered_file", orderedPaths.get(0).getFileName().toString());
            inputMeta.put("ordered_file_count", orderedPaths.size());
        }
        if (soldPath != null) {
            inputMeta.put("sold_file", soldPath.getFileName().toString());
        }
        run.setInputMetadata(inputMeta);
        runRepository.save(run);

        // --- Run items ---
        List<RunItemDocument> items = new ArrayList<>();
        for (Map<String, Object> rec : result.reconciled) {
            RunItemDocument item = new RunItemDocument();
            item.setRunId(runId);
            item.setUserId(userId);
            item.setMedicineKey(str(rec.get("medicine_key")));
            item.setDrugName(str(rec.get("drug_name")));
            item.setNdc(str(rec.get("ndc")));
            item.setStrength(str(rec.get("strength")));
            item.setManufacturer(str(rec.get("manufacturer")));
            item.setOrderedQty(dbl(rec.get("ordered_total")));
            item.setSoldQty(dbl(rec.get("sold_total")));
            item.setRemainingQty(dbl(rec.get("remaining_qty")));
            item.setShortageQty(dbl(rec.get("shortage_qty")));
            item.setLeftoverQty(dbl(rec.get("leftover_qty")));
            items.add(item);
        }
        if (!items.isEmpty()) {
            runItemRepository.saveAll(items);
        }

        // --- Run issues ---
        List<RunIssueDocument> issueDocs = new ArrayList<>();
        for (Map<String, Object> issue : result.issues) {
            RunIssueDocument doc = new RunIssueDocument();
            doc.setRunId(runId);
            doc.setUserId(userId);
            doc.setRuleId(str(issue.get("rule_id")));
            doc.setSeverity(str(issue.get("severity")));
            doc.setMedicineKey(str(issue.get("medicine_key")));
            doc.setDetails(str(issue.get("details")));
            if (issue.get("row_ref") instanceof Map<?,?> m) {
                @SuppressWarnings("unchecked") Map<String, Object> cast = (Map<String, Object>) m;
                doc.setRowRef(cast);
            }
            if (issue.get("raw_snippet") instanceof Map<?,?> m) {
                @SuppressWarnings("unchecked") Map<String, Object> cast = (Map<String, Object>) m;
                doc.setRawSnippet(cast);
            }
            issueDocs.add(doc);
        }
        if (!issueDocs.isEmpty()) {
            runIssueRepository.saveAll(issueDocs);
        }

        log.info("Persisted run {}: {} items, {} issues", runId, items.size(), issueDocs.size());
    }

    // ====================== EXISTING QUERY METHODS ======================

    public List<Map<String, Object>> listRuns(String userId, int limit, int offset) {
        Pageable page = PageRequest.of(offset / Math.max(limit, 1), limit);
        return runRepository.findByUserIdOrderByCreatedAtDesc(userId, page)
                .stream().map(this::runToMap).collect(Collectors.toList());
    }

    public long countRuns(String userId) {
        return runRepository.countByUserId(userId);
    }

    public Optional<RunDocument> getRun(String userId, String runId) {
        return runRepository.findByRunIdAndUserId(runId, userId);
    }

    public boolean deleteRun(String userId, String runId) {
        Optional<RunDocument> run = runRepository.findByRunIdAndUserId(runId, userId);
        if (run.isEmpty()) return false;
        runRepository.deleteByRunIdAndUserId(runId, userId);
        runItemRepository.deleteByRunIdAndUserId(runId, userId);
        runIssueRepository.deleteByRunIdAndUserId(runId, userId);
        return true;
    }

    public Path getRunOutputDir(String runId) {
        return outputDirPath.resolve(runId);
    }

    /** Find a downloadable file for a run, checking fallback dir. */
    public Optional<Path> getDownloadFile(String runId, String fileType) {
        Path primary = getRunOutputDir(runId).resolve(fileType);
        if (Files.exists(primary) && Files.isRegularFile(primary)) return Optional.of(primary);
        if (!fallbackOutputDir.isEmpty()) {
            Path fallback = Paths.get(fallbackOutputDir).resolve(runId).resolve(fileType);
            if (Files.exists(fallback) && Files.isRegularFile(fallback)) return Optional.of(fallback);
        }
        return Optional.empty();
    }

    /** Load report CSV as list of row maps; tries fallback dir. */
    public List<Map<String, Object>> loadReportCsv(String runId) throws IOException, CsvException {
        Path csvFile = getRunOutputDir(runId).resolve("inventory_report.csv");
        if (!Files.exists(csvFile) && !fallbackOutputDir.isEmpty()) {
            Path fallback = Paths.get(fallbackOutputDir).resolve(runId).resolve("inventory_report.csv");
            if (Files.exists(fallback)) csvFile = fallback;
        }
        if (!Files.exists(csvFile)) return Collections.emptyList();
        try (CSVReader reader = new CSVReaderBuilder(
                new InputStreamReader(Files.newInputStream(csvFile), StandardCharsets.UTF_8))
                .withSkipLines(0).build()) {
            List<String[]> rows = reader.readAll();
            if (rows.isEmpty()) return Collections.emptyList();
            String[] headers = rows.get(0);
            List<Map<String, Object>> result = new ArrayList<>();
            for (int i = 1; i < rows.size(); i++) {
                Map<String, Object> row = new LinkedHashMap<>();
                String[] values = rows.get(i);
                for (int j = 0; j < headers.length; j++) {
                    String val = j < values.length ? values[j] : "";
                    row.put(headers[j], val == null || val.isEmpty() ? null : val);
                }
                result.add(row);
            }
            return result;
        }
    }

    // ====================== MEDICINE DETAIL ======================

    /**
     * Medicine detail: load source_ordered.csv and source_sold.csv,
     * filter to medicine_key, return ordered/sold entries and report row.
     * Matches Python: GET /api/runs/{run_id}/medicine/{identifier}
     */
    public Map<String, Object> getMedicineDetail(String userId, String runId, String medicineIdentifier) {
        Optional<RunDocument> runOpt = getRun(userId, runId);
        if (runOpt.isEmpty()) return null;

        // Normalize the identifier
        String normalizedId = normalizeMedicineIdentifier(medicineIdentifier);

        // Load source data
        Path outputDir = resolveRunDir(runId);
        List<Map<String, Object>> orderedEntries = loadSourceEntries(outputDir.resolve("source_ordered.csv"), normalizedId);
        List<Map<String, Object>> soldEntries = loadSourceEntries(outputDir.resolve("source_sold.csv"), normalizedId);

        // Load report row
        Map<String, Object> reportRow = null;
        try {
            List<Map<String, Object>> report = loadReportCsv(runId);
            for (Map<String, Object> row : report) {
                if (matchesMedicineId(normalizedId, row)) {
                    reportRow = row;
                    break;
                }
            }
        } catch (Exception ignored) {}

        double totalOrdered = orderedEntries.stream()
                .mapToDouble(e -> dbl(e.get("ordered_qty"))).sum();
        double totalSold = soldEntries.stream()
                .mapToDouble(e -> dbl(e.get("sold_qty"))).sum();

        Map<String, Object> out = new LinkedHashMap<>();
        out.put("medicine_key", normalizedId);
        out.put("ordered_entries", formatEntries(orderedEntries, "ordered"));
        out.put("sold_entries", formatEntries(soldEntries, "sold"));
        out.put("total_ordered", totalOrdered);
        out.put("total_sold", totalSold);
        out.put("report_data", reportRow != null ? reportRow : Collections.emptyMap());
        return out;
    }

    // ====================== ADMIN AGGREGATION ======================

    @SuppressWarnings("rawtypes")
    public List<Map<String, Object>> getReportCountsByUserSince(Date since) {
        return getReportCountsByUser(since, null, null);
    }

    @SuppressWarnings("rawtypes")
    public List<Map<String, Object>> getReportCountsByUser(Date from, Date to, String userQuery) {
        Date fromDate = from, toDate = to;
        if (fromDate == null && toDate == null) {
            fromDate = new Date(System.currentTimeMillis() - TimeUnit.DAYS.toMillis(30));
            toDate = new Date();
        }
        if (fromDate == null) fromDate = new Date(0);
        if (toDate == null) toDate = new Date();

        Criteria criteria = Criteria.where("created_at").gte(fromDate).lte(toDate);
        if (userQuery != null && !userQuery.trim().isEmpty()) {
            String pattern = ".*" + userQuery.trim().replaceAll("([.*+?^${}()|\\[\\]\\\\])", "\\\\$1") + ".*";
            criteria = criteria.and("user_id").regex(pattern, "i");
        }
        MatchOperation match = Aggregation.match(criteria);
        GroupOperation group = Aggregation.group("user_id").count().as("report_count");
        SortOperation sort = Aggregation.sort(Sort.Direction.DESC, "report_count");
        ProjectionOperation project = Aggregation.project("report_count").and("_id").as("user_id");
        Aggregation agg = Aggregation.newAggregation(match, group, sort, project);
        AggregationResults results = mongoTemplate.aggregate(agg, RUNS_COLLECTION, Map.class);
        List<Map<String, Object>> list = new ArrayList<>();
        for (Object o : results.getMappedResults()) {
            Map m = (Map) o;
            Map<String, Object> row = new LinkedHashMap<>();
            row.put("user_id", m.get("user_id"));
            row.put("report_count", m.get("report_count"));
            list.add(row);
        }
        return list;
    }

    // ====================== HELPERS ======================

    private String generateRunId() {
        // Match Python: YYYYMMDD_HHMMSS_mmm
        java.time.LocalDateTime now = java.time.LocalDateTime.now();
        return now.format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss_SSS"));
    }

    private static String sanitizeFilename(String name) {
        if (name == null || name.isBlank()) return "file.csv";
        return name.replaceAll("[^a-zA-Z0-9._-]", "_");
    }

    /** Extract supplier name from filename like "ordered_0_1.akron_generics.csv" → "AKRON GENERICS". */
    static String extractSupplierName(String filename) {
        String stem = filename;
        int dot = stem.lastIndexOf('.');
        if (dot > 0) stem = stem.substring(0, dot);
        // Remove "ordered_X_" prefix
        if (stem.startsWith("ordered_")) {
            String[] parts = stem.split("_", 3);
            if (parts.length >= 3) stem = parts[2];
        }
        String supplier = stem.replace("_", " ").replace(".", " ").replace("-", " ");
        // Remove leading numbers
        supplier = Arrays.stream(supplier.split(" "))
                .filter(w -> !w.matches("\\d+"))
                .collect(Collectors.joining(" "));
        supplier = supplier.trim().toUpperCase(Locale.ROOT);
        return supplier.isEmpty() ? filename.toUpperCase(Locale.ROOT) : supplier;
    }

    /**
     * Date filtering to match Python (app.py): exclude rows with missing/unparseable date when filter is active.
     * Python: picks first present date column; drops rows where that column is NaT (notna()); then applies from/to.
     * So: if a date column exists in the data, rows with no parseable date are EXCLUDED; only include when date is in range.
     */
    private List<Map<String, Object>> filterByDate(
            List<Map<String, Object>> rows, List<String> dateFields,
            LocalDate from, LocalDate to) {
        if (from == null && to == null) return rows;
        if (rows.isEmpty()) return rows;
        // Choose first date field that exists in the dataset (match Python: "col in ordered_normalized.columns")
        Set<String> allKeys = new HashSet<>();
        for (Map<String, Object> r : rows) allKeys.addAll(r.keySet());
        String dateField = null;
        for (String f : dateFields) {
            if (allKeys.contains(f)) {
                dateField = f;
                break;
            }
        }
        if (dateField == null) {
            log.warn("No date column found in data (checked {}); date filter not applied", dateFields);
            return rows;
        }
        final String chosen = dateField;
        return rows.stream().filter(row -> {
            Object v = row.get(chosen);
            if (v == null || String.valueOf(v).isBlank()) return false;
            LocalDate d = parseIsoDate(String.valueOf(v));
            if (d == null) return false;
            if (from != null && d.isBefore(from)) return false;
            if (to != null && d.isAfter(to)) return false;
            return true;
        }).collect(Collectors.toList());
    }

    private static LocalDate parseIsoDate(String s) {
        if (s == null || s.isBlank()) return null;
        try {
            return LocalDate.parse(s.trim());
        } catch (DateTimeParseException e) {
            return null;
        }
    }

    /** Write normalized rows to a CSV (for medicine detail later). */
    private void writeSourceCsv(Path path, List<Map<String, Object>> rows) throws IOException {
        if (rows.isEmpty()) {
            Files.createFile(path);
            return;
        }
        // Collect all column names preserving order
        Set<String> colSet = new LinkedHashSet<>();
        for (Map<String, Object> r : rows) colSet.addAll(r.keySet());
        List<String> cols = new ArrayList<>(colSet);

        try (CSVWriter w = new CSVWriter(
                new OutputStreamWriter(Files.newOutputStream(path), StandardCharsets.UTF_8))) {
            w.writeNext(cols.toArray(new String[0]));
            for (Map<String, Object> r : rows) {
                String[] vals = new String[cols.size()];
                for (int i = 0; i < cols.size(); i++) {
                    Object v = r.get(cols.get(i));
                    vals[i] = v == null ? "" : String.valueOf(v);
                }
                w.writeNext(vals);
            }
        }
    }

    private void writeSummaryJson(Path path, Map<String, Object> summary,
                                   String reportName, String dateFrom, String dateTo) {
        try {
            StringBuilder sb = new StringBuilder("{\n");
            if (reportName != null) sb.append("  \"report_name\": \"").append(reportName).append("\",\n");
            if (dateFrom != null) sb.append("  \"date_from\": \"").append(dateFrom).append("\",\n");
            if (dateTo != null) sb.append("  \"date_to\": \"").append(dateTo).append("\",\n");
            for (var e : summary.entrySet()) {
                sb.append("  \"").append(e.getKey()).append("\": ");
                Object v = e.getValue();
                if (v instanceof Number) sb.append(v);
                else sb.append("\"").append(v).append("\"");
                sb.append(",\n");
            }
            if (sb.length() > 2) sb.setLength(sb.length() - 2); // remove trailing comma
            sb.append("\n}");
            Files.writeString(path, sb.toString(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            log.warn("Failed to write summary.json: {}", e.getMessage());
        }
    }

    /** Resolve run output dir, checking fallback. */
    private Path resolveRunDir(String runId) {
        Path primary = getRunOutputDir(runId);
        if (Files.isDirectory(primary)) return primary;
        if (!fallbackOutputDir.isEmpty()) {
            Path fallback = Paths.get(fallbackOutputDir).resolve(runId);
            if (Files.isDirectory(fallback)) return fallback;
        }
        return primary;
    }

    /** Load source CSV and filter to rows matching the medicine identifier. */
    private List<Map<String, Object>> loadSourceEntries(Path csvPath, String normalizedId) {
        if (!Files.exists(csvPath)) return Collections.emptyList();
        try (CSVReader reader = new CSVReaderBuilder(
                new InputStreamReader(Files.newInputStream(csvPath), StandardCharsets.UTF_8))
                .withSkipLines(0).build()) {
            List<String[]> all = reader.readAll();
            if (all.size() < 2) return Collections.emptyList();
            String[] headers = all.get(0);
            List<Map<String, Object>> entries = new ArrayList<>();
            for (int i = 1; i < all.size(); i++) {
                Map<String, Object> row = new LinkedHashMap<>();
                String[] vals = all.get(i);
                for (int j = 0; j < headers.length; j++) {
                    String v = j < vals.length ? vals[j] : "";
                    row.put(headers[j], v.isEmpty() ? null : v);
                }
                if (matchesMedicineId(normalizedId, row)) {
                    entries.add(row);
                }
            }
            return entries;
        } catch (Exception e) {
            log.warn("Failed to load source CSV {}: {}", csvPath, e.getMessage());
            return Collections.emptyList();
        }
    }

    private String normalizeMedicineIdentifier(String id) {
        if (id == null) return "";
        String trimmed = id.trim();
        if (trimmed.startsWith("NDC:") || trimmed.startsWith("COMPOSITE:")) return trimmed;
        String normalized = NdcNormalizer.normalize(trimmed);
        if (normalized != null) return "NDC:" + normalized;
        return trimmed;
    }

    private static boolean matchesMedicineId(String normalizedId, Map<String, Object> row) {
        String key = str(row.get("medicine_key"));
        if (key.equalsIgnoreCase(normalizedId)) return true;
        String ndc = str(row.get("NDC"));
        if (!ndc.isEmpty()) {
            String ndcDigits = ndc.replaceAll("\\D", "");
            String idDigits = normalizedId.replaceAll("\\D", "");
            if (!ndcDigits.isEmpty() && ndcDigits.equals(idDigits)) return true;
        }
        String drugName = str(row.get("DRUG NAME"));
        if (!drugName.isEmpty() && drugName.equalsIgnoreCase(normalizedId)) return true;
        String dn2 = str(row.get("drug_name"));
        if (!dn2.isEmpty() && dn2.equalsIgnoreCase(normalizedId)) return true;
        return false;
    }

    private List<Map<String, Object>> formatEntries(List<Map<String, Object>> raw, String type) {
        List<Map<String, Object>> formatted = new ArrayList<>();
        for (Map<String, Object> r : raw) {
            Map<String, Object> e = new LinkedHashMap<>();
            // Date
            if ("ordered".equals(type)) {
                e.put("date", firstNonNull(r, "order_date", "invoice_date", "purchase_date", "claim_date"));
                e.put("source_type", "ordered");
                e.put("source_name", str(r.get("supplier_name")));
                e.put("quantity", dbl(r.get("ordered_qty")));
            } else {
                e.put("date", firstNonNull(r, "claim_date", "date_filled", "fill_date"));
                e.put("source_type", "sold");
                e.put("source_name", "");
                e.put("quantity", dbl(r.get("sold_qty")));
            }
            e.put("ndc", str(r.get("ndc")));
            e.put("drug_name", str(r.get("drug_name")));
            e.put("strength", str(r.get("strength")));
            e.put("manufacturer", str(r.get("manufacturer")));
            e.put("supplier_name", str(r.get("supplier_name")));
            formatted.add(e);
        }
        return formatted;
    }

    private static String firstNonNull(Map<String, Object> m, String... keys) {
        for (String k : keys) {
            String v = str(m.get(k));
            if (!v.isEmpty()) return v;
        }
        return "";
    }

    private Map<String, Object> runToMap(RunDocument r) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("run_id", r.getRunId());
        m.put("user_id", r.getUserId());
        m.put("created_at", r.getCreatedAt() != null ? r.getCreatedAt().toInstant().toString() : null);
        m.put("config_summary", r.getConfigSummary());
        m.put("stats", r.getStats());
        m.put("input_metadata", r.getInputMetadata());
        return m;
    }

    private static String str(Object o) {
        if (o == null) return "";
        return String.valueOf(o).trim();
    }

    private static double dbl(Object o) {
        if (o == null) return 0;
        if (o instanceof Number n) return n.doubleValue();
        try {
            return Double.parseDouble(String.valueOf(o).trim().replace(",", ""));
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    // ---- Inner class for pipeline result ----
    static class PipelineResult {
        List<Map<String, Object>> reconciled = Collections.emptyList();
        Map<String, Object> summary = Collections.emptyMap();
        List<Map<String, Object>> issues = Collections.emptyList();
        List<Map<String, Object>> dawairxReport = Collections.emptyList();
        List<String> dawairxColumns = Collections.emptyList();
    }
}
