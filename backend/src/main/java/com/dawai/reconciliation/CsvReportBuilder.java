package com.dawai.reconciliation;

import com.opencsv.CSVReader;
import com.opencsv.CSVReaderBuilder;
import com.opencsv.CSVWriter;
import com.opencsv.exceptions.CsvException;

import java.io.IOException;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import java.util.regex.Pattern;

/**
 * Parses uploaded ordered/sold CSVs and builds inventory_report.csv from reconciliation result.
 */
public final class CsvReportBuilder {

    private static final Pattern NON_DIGIT = Pattern.compile("\\D");

    /** Normalize NDC to 11 digits; return null if invalid. */
    public static String normalizeNdc(String ndc) {
        if (ndc == null || ndc.isBlank()) return null;
        String digits = NON_DIGIT.matcher(ndc).replaceAll("");
        return digits.length() == 11 ? digits : null;
    }

    /** Format NDC for display: 12345-678-90 */
    public static String formatNdcDisplay(String ndc11) {
        if (ndc11 == null || ndc11.length() != 11) return ndc11 != null ? ndc11 : "";
        return ndc11.substring(0, 5) + "-" + ndc11.substring(5, 9) + "-" + ndc11.substring(9);
    }

    /** Build medicine_key: NDC:11digits or COMPOSITE:name|strength|mfr */
    public static String medicineKey(String ndc, String drugName, String strength, String manufacturer) {
        String n = normalizeNdc(ndc);
        if (n != null) return "NDC:" + n;
        List<String> parts = new ArrayList<>();
        if (drugName != null && !(drugName = drugName.trim()).isEmpty()) parts.add(normalizeForKey(drugName));
        if (strength != null && !(strength = strength.trim()).isEmpty()) parts.add(normalizeForKey(strength));
        if (manufacturer != null && !(manufacturer = manufacturer.trim()).isEmpty()) parts.add(normalizeForKey(manufacturer));
        if (parts.isEmpty()) return "UNKNOWN";
        return "COMPOSITE:" + String.join("|", parts);
    }

    private static String normalizeForKey(String s) {
        return s.trim().toUpperCase(Locale.ROOT).replaceAll("\\s+", " ");
    }

    /** Find header index by possible names (case-insensitive). */
    public static int findColumn(String[] headers, String... names) {
        for (int i = 0; i < headers.length; i++) {
            String h = headers[i] != null ? headers[i].trim().toLowerCase(Locale.ROOT) : "";
            for (String n : names) {
                if (n != null && h.equals(n.toLowerCase(Locale.ROOT))) return i;
                if (n != null && h.contains(n.toLowerCase(Locale.ROOT))) return i;
            }
        }
        return -1;
    }

    public static String get(String[] row, int index) {
        if (index < 0 || index >= row.length) return "";
        String s = row[index];
        return s != null ? s.trim() : "";
    }

    public static double getDouble(String[] row, int index) {
        String s = get(row, index);
        if (s.isEmpty()) return 0;
        try {
            return Double.parseDouble(s.replace(",", ""));
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    /**
     * Parse a CSV into rows for reconciliation.
     * For ordered: maps have medicine_key, drug_name, strength, manufacturer, ndc, ordered_qty.
     * For sold: maps have medicine_key, drug_name, strength, manufacturer, ndc, sold_qty.
     */
    public static List<Map<String, Object>> parseCsvForReconciliation(Path csvPath, boolean isOrdered) throws IOException, CsvException {
        List<Map<String, Object>> rows = new ArrayList<>();
        try (CSVReader reader = new CSVReaderBuilder(Files.newBufferedReader(csvPath, StandardCharsets.UTF_8))
                .withSkipLines(0)
                .build()) {
            List<String[]> all = reader.readAll();
            if (all.isEmpty()) return rows;
            String[] headers = all.get(0);
            int ndcCol = findColumn(headers, "ndc", "ndc code", "ndc_code");
            int drugCol = findColumn(headers, "drug name", "drug_name", "item description", "description", "product name");
            int strengthCol = findColumn(headers, "strength");
            int mfrCol = findColumn(headers, "manufacturer", "mfr", "maker");
            int qtyCol;
            if (isOrdered) {
                qtyCol = findColumn(headers, "ordered_qty", "ordered qty", "quantity", "qty", "units");
                if (qtyCol < 0) qtyCol = findColumn(headers, "qty ordered", "quantity ordered");
            } else {
                qtyCol = findColumn(headers, "sold_qty", "sold qty", "billed", "quantity", "qty", "units");
            }

            for (int i = 1; i < all.size(); i++) {
                String[] row = all.get(i);
                String ndc = get(row, ndcCol);
                String drugName = drugCol >= 0 ? get(row, drugCol) : "";
                String strength = strengthCol >= 0 ? get(row, strengthCol) : "";
                String mfr = mfrCol >= 0 ? get(row, mfrCol) : "";
                String key = medicineKey(ndc, drugName, strength, mfr);
                if ("UNKNOWN".equals(key)) continue;
                double qty = getDouble(row, qtyCol);
                Map<String, Object> map = new LinkedHashMap<>();
                map.put("medicine_key", key);
                map.put("drug_name", drugName.isEmpty() ? ndc : drugName);
                map.put("strength", strength);
                map.put("manufacturer", mfr);
                map.put("ndc", ndc);
                if (isOrdered) {
                    map.put("ordered_qty", qty);
                } else {
                    map.put("sold_qty", qty);
                }
                rows.add(map);
            }
        }
        return rows;
    }

    /**
     * Write reconciliation result to inventory_report.csv (DawaiRx-style columns).
     */
    public static void writeInventoryReport(Path outputCsv, List<Map<String, Object>> reconciled) throws IOException {
        if (reconciled == null || reconciled.isEmpty()) {
            Files.createDirectories(outputCsv.getParent());
            try (CSVWriter w = new CSVWriter(new OutputStreamWriter(Files.newOutputStream(outputCsv), StandardCharsets.UTF_8))) {
                w.writeNext(new String[]{"NDC", "DRUG NAME", "RANK", "PKG SIZE", "TOTAL ORDERED-O", "TOTAL BILLED-B", "TOTAL SHORTAGE-S", "AMOUNT", "COST", "medicine_key"});
            }
            return;
        }

        // Sort by sold_total desc, then by shortage for display
        List<Map<String, Object>> sorted = new ArrayList<>(reconciled);
        sorted.sort((a, b) -> {
            double sa = getNum(a, "sold_total");
            double sb = getNum(b, "sold_total");
            if (sa != sb) return Double.compare(sb, sa);
            return Double.compare(getNum(b, "shortage_qty"), getNum(a, "shortage_qty"));
        });

        int rank = 1;
        List<String> headers = Arrays.asList(
                "NDC", "DRUG NAME", "RANK", "PKG SIZE",
                "TOTAL ORDERED-O", "TOTAL BILLED-B", "TOTAL SHORTAGE-S",
                "AMOUNT", "COST", "medicine_key");
        Files.createDirectories(outputCsv.getParent());
        try (CSVWriter w = new CSVWriter(new OutputStreamWriter(Files.newOutputStream(outputCsv), StandardCharsets.UTF_8))) {
            w.writeNext(headers.toArray(new String[0]));
            for (Map<String, Object> row : sorted) {
                String ndc = String.valueOf(row.get("ndc"));
                if (normalizeNdc(ndc) != null) ndc = formatNdcDisplay(normalizeNdc(ndc));
                String drugName = String.valueOf(row.getOrDefault("drug_name", ""));
                double orderedTotal = getNum(row, "ordered_total");
                double soldTotal = getNum(row, "sold_total");
                double shortage = getNum(row, "shortage_qty");
                String medicineKey = String.valueOf(row.getOrDefault("medicine_key", ""));
                w.writeNext(new String[]{
                        ndc,
                        drugName,
                        String.valueOf(rank++),
                        "1",
                        formatNum(orderedTotal),
                        formatNum(soldTotal),
                        formatNum(shortage),
                        formatNum(soldTotal),
                        formatNum(orderedTotal),
                        medicineKey
                });
            }
        }
    }

    private static double getNum(Map<String, Object> m, String key) {
        Object v = m.get(key);
        if (v instanceof Number n) return n.doubleValue();
        if (v == null) return 0;
        try {
            return Double.parseDouble(String.valueOf(v));
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    private static String formatNum(double d) {
        if (d == (long) d) return String.valueOf((long) d);
        return String.format("%.2f", d);
    }
}
