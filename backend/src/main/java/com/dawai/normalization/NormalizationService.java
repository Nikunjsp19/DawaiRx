package com.dawai.normalization;

import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.*;
import java.util.regex.Pattern;

/**
 * Normalizes ingested data rows to canonical form.
 * Must match Python: src/normalization/processor.py  normalize_dataframe()
 *
 * Steps for each row:
 *  1. NDC: normalize to 11 digits, preserve original as ndc_original
 *  2. Text: drug_name, strength, manufacturer → UPPERCASE (preserve _original)
 *  3. Quantity: parse to double (remove $, commas)
 *  4. Date: parse claim_date / order_date / invoice_date → ISO date string
 *  5. Medicine key: generate from (ndc, drug_name, strength, manufacturer)
 */
@Service
public class NormalizationService {

    private static final Pattern AMOUNT_STRIP = Pattern.compile("[^0-9.\\-]");
    private static final List<DateTimeFormatter> DATE_PARSERS = List.of(
            DateTimeFormatter.ofPattern("M/d/yyyy"),
            DateTimeFormatter.ofPattern("MM/dd/yyyy"),
            DateTimeFormatter.ofPattern("yyyy-MM-dd"),
            DateTimeFormatter.ofPattern("M-d-yyyy"),
            DateTimeFormatter.ofPattern("MM-dd-yyyy"),
            DateTimeFormatter.ofPattern("yyyyMMdd"),
            DateTimeFormatter.ofPattern("M/d/yy"),
            DateTimeFormatter.ofPattern("MM/dd/yy")
    );

    /**
     * Normalize a list of raw rows (from FileLoader + ColumnMapper).
     *
     * @param rows       raw rows with canonical column names
     * @param reportType "ordered" or "sold"
     * @return normalized rows with medicine_key and preserved originals
     */
    public List<Map<String, Object>> normalize(List<? extends Map<String, ?>> rows, String reportType) {
        List<Map<String, Object>> result = new ArrayList<>(rows.size());
        for (Map<String, ?> raw : rows) {
            result.add(normalizeRow(raw, reportType));
        }
        return result;
    }

    private Map<String, Object> normalizeRow(Map<String, ?> raw, String reportType) {
        Map<String, Object> r = new LinkedHashMap<>();
        // copy all original values
        raw.forEach((k, v) -> r.put(k, v));

        // --- NDC ---
        if (r.containsKey("ndc")) {
            String orig = str(r.get("ndc"));
            r.put("ndc_original", orig);
            String norm = NdcNormalizer.normalize(orig);
            r.put("ndc", norm != null ? norm : orig);
            r.put("ndc_normalized", norm);
        }

        // --- Text fields ---
        preserveAndNormText(r, "drug_name");
        preserveAndNormText(r, "strength");
        preserveAndNormText(r, "manufacturer");

        // --- Quantities ---
        String qtyField = "ordered".equals(reportType) ? "ordered_qty" : "sold_qty";
        if (r.containsKey(qtyField)) {
            r.put(qtyField + "_original", r.get(qtyField));
            r.put(qtyField, parseQuantity(r.get(qtyField)));
        } else if (r.containsKey("quantity")) {
            r.put("quantity_original", r.get("quantity"));
            r.put(qtyField, parseQuantity(r.get("quantity")));
        }

        // pkg_size: parse to double if present
        if (r.containsKey("pkg_size")) {
            r.put("pkg_size", parseQuantity(r.get("pkg_size")));
        }

        // insurance paid: parse to double
        for (String f : List.of("primary_insurance_paid", "secondary_insurance_paid")) {
            if (r.containsKey(f)) {
                r.put(f, parseQuantity(r.get(f)));
            }
        }

        // --- Dates ---
        if ("sold".equals(reportType)) {
            normalizeDateField(r, "claim_date", "date_filled", "fill_date", "dispense_date");
        } else {
            normalizeDateField(r, "order_date", "invoice_date", "purchase_date", "claim_date", "date_filled");
        }

        // --- Medicine key ---
        r.put("medicine_key", MedicineKeyGenerator.generate(
                str(r.get("ndc")),
                str(r.get("drug_name")),
                str(r.get("strength")),
                str(r.get("manufacturer"))
        ));

        return r;
    }

    /** Preserve original and normalize text to UPPERCASE (matching Python normalize_text). */
    private void preserveAndNormText(Map<String, Object> r, String field) {
        if (!r.containsKey(field)) return;
        String orig = str(r.get(field));
        r.put(field + "_original", orig);
        r.put(field, normalizeText(orig));
    }

    /**
     * Matches Python normalize_text(text, case="upper"):
     *  strip, reject null-like, collapse spaces, UPPERCASE.
     */
    static String normalizeText(String s) {
        if (s == null) return null;
        String t = s.trim();
        if (t.isEmpty()) return null;
        String lower = t.toLowerCase(Locale.ROOT);
        if ("nan".equals(lower) || "none".equals(lower) || "null".equals(lower)) return null;
        return t.replaceAll("\\s+", " ").toUpperCase(Locale.ROOT);
    }

    /** Parse a quantity value (string or number) to double, 0 if unparseable. */
    static double parseQuantity(Object o) {
        if (o == null) return 0;
        if (o instanceof Number n) return n.doubleValue();
        String s = String.valueOf(o).trim();
        if (s.isEmpty() || "nan".equalsIgnoreCase(s) || "none".equalsIgnoreCase(s)) return 0;
        String cleaned = AMOUNT_STRIP.matcher(s).replaceAll("");
        if (cleaned.isEmpty()) return 0;
        try {
            return Double.parseDouble(cleaned);
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    /** Try to parse dates from first found field; copy to canonical field if needed. */
    private void normalizeDateField(Map<String, Object> r, String... fieldNames) {
        for (String field : fieldNames) {
            if (r.containsKey(field)) {
                String orig = str(r.get(field));
                r.put(field + "_original", orig);
                String parsed = parseDate(orig);
                if (parsed != null) {
                    r.put(field, parsed);
                    // copy to canonical: claim_date for sold, order_date for ordered
                    if ("date_filled".equals(field) && !r.containsKey("claim_date")) {
                        r.put("claim_date", parsed);
                    }
                    if ("invoice_date".equals(field) && !r.containsKey("order_date")) {
                        r.put("order_date", parsed);
                    }
                }
                return; // stop at first found
            }
        }
    }

    /** Parse a date string to ISO format (yyyy-MM-dd). Returns null if unparseable. */
    static String parseDate(String s) {
        if (s == null || s.isBlank()) return null;
        String trimmed = s.trim();
        if (trimmed.toLowerCase(Locale.ROOT).matches("nan|none|null")) return null;
        // Try each parser
        for (DateTimeFormatter fmt : DATE_PARSERS) {
            try {
                LocalDate d = LocalDate.parse(trimmed, fmt);
                return d.toString(); // yyyy-MM-dd
            } catch (DateTimeParseException ignored) {}
        }
        // Try ISO parse as fallback
        try {
            return LocalDate.parse(trimmed).toString();
        } catch (DateTimeParseException ignored) {}
        return null;
    }

    private static String str(Object o) {
        return o == null ? "" : String.valueOf(o).trim();
    }
}
