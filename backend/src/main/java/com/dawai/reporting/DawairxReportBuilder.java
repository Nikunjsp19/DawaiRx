package com.dawai.reporting;

import com.dawai.normalization.NdcNormalizer;
import com.opencsv.CSVWriter;

import java.io.IOException;
import java.io.OutputStreamWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

/**
 * Builds the DawaiRx-style inventory report CSV.
 * Must match Python: src/reporting/dawairx_format.py  create_dawairx_report()
 *
 * Column format:
 *  NDC, DRUG NAME, RANK, PKG SIZE,
 *  TOTAL\nORDERED-O, TOTAL\nBILLED-B, TOTAL\nSHORTAGE-S, HIGHEST\nSHORTAGE-S,
 *  AMOUNT, COST,
 *  BILLED\n{insurance}-B / SHORTAGE\n{insurance}-S  (dynamic),
 *  ORDERED\n{supplier}-O  (dynamic),
 *  medicine_key
 */
public class DawairxReportBuilder {

    /**
     * Build and write the DawaiRx report CSV.
     *
     * @param outputCsv        path to write inventory_report.csv
     * @param reconciled        reconciled rows (medicine_key, drug_name, ndc, ordered_total, sold_total, shortage_qty, ...)
     * @param soldNormalized    normalized sold rows (medicine_key, sold_qty, primary_insurance_paid/name, secondary_..., pkg_size, drug_name_original)
     * @param orderedNormalized normalized ordered rows (medicine_key, ordered_qty, pkg_size, supplier_name, cost/unit_cost/...)
     * @param allSupplierNames  supplier names from BEFORE date filtering (ensures columns appear even if all zeros)
     * @return list of report row maps (for JSON response / run items)
     */
    public static List<Map<String, Object>> buildAndWrite(
            Path outputCsv,
            List<Map<String, Object>> reconciled,
            List<Map<String, Object>> soldNormalized,
            List<Map<String, Object>> orderedNormalized,
            List<String> allSupplierNames
    ) throws IOException {

        if (reconciled == null || reconciled.isEmpty()) {
            writeEmpty(outputCsv);
            return Collections.emptyList();
        }

        // --- 1. Start with reconciled data, build report rows ---
        List<Map<String, Object>> report = new ArrayList<>();
        for (Map<String, Object> r : reconciled) {
            Map<String, Object> row = new LinkedHashMap<>();
            String key = str(r.get("medicine_key"));
            row.put("medicine_key", key);

            // NDC display
            String ndc = str(r.get("ndc"));
            String normNdc = NdcNormalizer.normalize(ndc);
            row.put("NDC", normNdc != null ? NdcNormalizer.formatDisplay(normNdc) : ndc);

            row.put("DRUG NAME", str(r.get("drug_name")));
            row.put("ordered_total_raw", dbl(r.get("ordered_total")));
            row.put("sold_total_raw", dbl(r.get("sold_total")));
            row.put("shortage_qty_raw", dbl(r.get("shortage_qty")));
            report.add(row);
        }

        // --- 2. Merge drug name from sold data (prefer original) ---
        Map<String, String> drugNameFromSold = new LinkedHashMap<>();
        for (Map<String, Object> s : soldNormalized) {
            String key = str(s.get("medicine_key"));
            if (key.isEmpty()) continue;
            if (drugNameFromSold.containsKey(key)) continue; // first wins
            String orig = str(s.get("drug_name_original"));
            if (orig.isEmpty()) orig = str(s.get("drug_name"));
            if (!orig.isEmpty()) drugNameFromSold.put(key, orig);
        }
        for (Map<String, Object> row : report) {
            String fromSold = drugNameFromSold.get(str(row.get("medicine_key")));
            if (fromSold != null && !fromSold.isEmpty()) {
                row.put("DRUG NAME", fromSold);
            }
        }

        // --- 3. PKG SIZE from sold data ---
        Map<String, Double> pkgSizeMap = new LinkedHashMap<>();
        for (Map<String, Object> s : soldNormalized) {
            String key = str(s.get("medicine_key"));
            if (key.isEmpty() || pkgSizeMap.containsKey(key)) continue;
            double ps = dbl(s.get("pkg_size"));
            if (ps > 0) pkgSizeMap.put(key, ps);
        }
        for (Map<String, Object> row : report) {
            double ps = pkgSizeMap.getOrDefault(str(row.get("medicine_key")), 1.0);
            row.put("PKG SIZE", ps > 0 ? ps : 1.0);
        }

        // --- 4. Collect medicine keys with sales (TOTAL BILLED-B > 0) ---
        Set<String> keysWithSales = new HashSet<>();
        for (Map<String, Object> row : report) {
            if (dbl(row.get("sold_total_raw")) > 0) {
                keysWithSales.add(str(row.get("medicine_key")));
            }
        }

        // --- 5. Calculate TOTAL ORDERED-O (units = ordered_qty * pkg_size, only for medicines with sales) ---
        // Aggregate from ordered data, filtered to medicines with sales
        Map<String, Double> orderedUnitsMap = new LinkedHashMap<>();
        for (Map<String, Object> o : orderedNormalized) {
            String key = str(o.get("medicine_key"));
            if (!keysWithSales.contains(key)) continue;
            double qty = dbl(o.get("ordered_qty"));
            double ps = dbl(o.get("pkg_size"));
            if (ps <= 0) ps = 1;
            orderedUnitsMap.merge(key, qty * ps, Double::sum);
        }
        for (Map<String, Object> row : report) {
            String key = str(row.get("medicine_key"));
            row.put("TOTAL\nORDERED-O", orderedUnitsMap.getOrDefault(key, 0.0));
        }

        // --- 6. TOTAL BILLED-B (from reconciled sold_total) ---
        for (Map<String, Object> row : report) {
            row.put("TOTAL\nBILLED-B", dbl(row.get("sold_total_raw")));
        }

        // --- 7. TOTAL SHORTAGE-S = TOTAL ORDERED - TOTAL BILLED (recalculated) ---
        for (Map<String, Object> row : report) {
            double ordered = dbl(row.get("TOTAL\nORDERED-O"));
            double billed = dbl(row.get("TOTAL\nBILLED-B"));
            row.put("TOTAL\nSHORTAGE-S", ordered - billed);
        }

        // --- 8. HIGHEST SHORTAGE-S: only negative values (leftovers), NaN for positive/zero ---
        for (Map<String, Object> row : report) {
            double shortage = dbl(row.get("TOTAL\nSHORTAGE-S"));
            row.put("HIGHEST\nSHORTAGE-S", shortage < 0 ? shortage : null);
        }

        // --- 9. AMOUNT = floor(sum of primary_insurance_paid + secondary_insurance_paid) per medicine ---
        Map<String, Double> insuranceTotals = new LinkedHashMap<>();
        for (Map<String, Object> s : soldNormalized) {
            String key = str(s.get("medicine_key"));
            if (key.isEmpty()) continue;
            double primary = dbl(s.get("primary_insurance_paid"));
            double secondary = dbl(s.get("secondary_insurance_paid"));
            insuranceTotals.merge(key, primary + secondary, Double::sum);
        }
        for (Map<String, Object> row : report) {
            String key = str(row.get("medicine_key"));
            double total = insuranceTotals.getOrDefault(key, 0.0);
            // CRITICAL: floor() not round() — 11.75 → 11
            row.put("AMOUNT", (int) Math.floor(total));
        }

        // --- 10. COST: from ordered data cost fields, else AMOUNT ---
        String costCol = detectCostField(orderedNormalized);
        Map<String, Double> costMap = new LinkedHashMap<>();
        if (costCol != null) {
            boolean isTotalCost = costCol.contains("total") || costCol.contains("extended");
            for (Map<String, Object> o : orderedNormalized) {
                String key = str(o.get("medicine_key"));
                if (!keysWithSales.contains(key)) continue;
                double cost;
                if (isTotalCost) {
                    cost = dbl(o.get(costCol));
                } else {
                    cost = dbl(o.get(costCol)) * dbl(o.get("ordered_qty"));
                }
                costMap.merge(key, cost, Double::sum);
            }
        }
        for (Map<String, Object> row : report) {
            String key = str(row.get("medicine_key"));
            Double cost = costMap.get(key);
            if (cost != null) {
                row.put("COST", Math.round(cost * 100.0) / 100.0); // round to 2 decimals
            } else {
                row.put("COST", row.get("AMOUNT")); // fallback to AMOUNT
            }
        }

        // --- 11. Filter: only medicines with TOTAL BILLED-B > 0 ---
        report.removeIf(row -> dbl(row.get("TOTAL\nBILLED-B")) <= 0);

        // --- 12. Sort by AMOUNT desc, COST desc, then assign RANK ---
        report.sort((a, b) -> {
            int c = Double.compare(dbl(b.get("AMOUNT")), dbl(a.get("AMOUNT")));
            if (c != 0) return c;
            return Double.compare(dbl(b.get("COST")), dbl(a.get("COST")));
        });
        for (int i = 0; i < report.size(); i++) {
            report.get(i).put("RANK", i + 1);
        }

        // --- 13. Insurance breakdown columns ---
        // Collect unique insurance names from both primary and secondary.
        // Normalize for column headers to match Python/legacy; aggregate by normalized name so one column per display name.
        Set<String> insuranceNamesRaw = new LinkedHashSet<>();
        for (Map<String, Object> s : soldNormalized) {
            addIfPresent(insuranceNamesRaw, s, "primary_insurance_name");
            addIfPresent(insuranceNamesRaw, s, "secondary_insurance_name");
        }
        // Order by normalized (display) name, one entry per display name (merge raw names that map to same)
        Map<String, List<String>> displayToRaw = new LinkedHashMap<>();
        for (String raw : insuranceNamesRaw) {
            String display = normalizeInsuranceName(raw);
            displayToRaw.computeIfAbsent(display, x -> new ArrayList<>()).add(raw);
        }
        List<String> insuranceNames = new ArrayList<>(displayToRaw.keySet());

        for (String displayName : insuranceNames) {
            List<String> rawNames = displayToRaw.get(displayName);
            String billedCol = "BILLED\n" + displayName + "-B";
            String shortageCol = "SHORTAGE\n" + displayName + "-S";

            // Aggregate sold_qty where insurance matches any raw name that maps to this display name
            Map<String, Double> insBilled = new LinkedHashMap<>();
            for (Map<String, Object> s : soldNormalized) {
                String key = str(s.get("medicine_key"));
                String prim = str(s.get("primary_insurance_name"));
                String sec = str(s.get("secondary_insurance_name"));
                boolean match = rawNames.stream().anyMatch(r -> r.equals(prim) || r.equals(sec));
                if (match) {
                    insBilled.merge(key, dbl(s.get("sold_qty")), Double::sum);
                }
            }

            for (Map<String, Object> row : report) {
                String key = str(row.get("medicine_key"));
                double billed = insBilled.getOrDefault(key, 0.0);
                row.put(billedCol, billed);
                double totalBilled = dbl(row.get("TOTAL\nBILLED-B"));
                double totalShortage = dbl(row.get("TOTAL\nSHORTAGE-S"));
                double shortageShare = (totalBilled != 0) ? (billed / totalBilled) * totalShortage : 0;
                row.put(shortageCol, shortageShare);
            }
        }

        // --- 14. Supplier columns ---
        List<String> suppliers = allSupplierNames != null ? allSupplierNames : new ArrayList<>();
        if (suppliers.isEmpty()) {
            // fallback: extract from ordered data
            Set<String> seen = new LinkedHashSet<>();
            for (Map<String, Object> o : orderedNormalized) {
                String sn = str(o.get("supplier_name"));
                if (!sn.isEmpty()) seen.add(sn);
            }
            suppliers = new ArrayList<>(seen);
        }

        for (String supplier : suppliers) {
            String normalized = supplier.replaceFirst("^SUPPLIER ", "").trim();
            String colName = "ORDERED\n" + normalized + "-O";

            // Aggregate ordered units for this supplier (filtered to medicines with sales)
            Map<String, Double> supUnits = new LinkedHashMap<>();
            for (Map<String, Object> o : orderedNormalized) {
                String sn = str(o.get("supplier_name"));
                if (!sn.equals(supplier)) continue;
                String key = str(o.get("medicine_key"));
                if (!keysWithSales.contains(key)) continue;
                double qty = dbl(o.get("ordered_qty"));
                double ps = dbl(o.get("pkg_size"));
                if (ps <= 0) ps = 1;
                supUnits.merge(key, qty * ps, Double::sum);
            }

            for (Map<String, Object> row : report) {
                row.put(colName, supUnits.getOrDefault(str(row.get("medicine_key")), 0.0));
            }
        }

        // --- 15. Column ordering ---
        List<String> baseColumns = List.of(
                "NDC", "DRUG NAME", "RANK", "PKG SIZE",
                "TOTAL\nORDERED-O", "TOTAL\nBILLED-B", "TOTAL\nSHORTAGE-S",
                "HIGHEST\nSHORTAGE-S", "AMOUNT", "COST");

        // Insurance columns (non-CASH first, sorted; CASH at end). Use normalized names for headers.
        List<String> insColumns = new ArrayList<>();
        List<String> cashColumns = new ArrayList<>();
        for (String ins : insuranceNames) {
            String displayName = normalizeInsuranceName(ins);
            String b = "BILLED\n" + displayName + "-B";
            String s = "SHORTAGE\n" + displayName + "-S";
            if (ins.toUpperCase(Locale.ROOT).contains("CASH")) {
                cashColumns.add(b);
                cashColumns.add(s);
            } else {
                insColumns.add(b);
                insColumns.add(s);
            }
        }

        // Supplier columns (predefined order then alphabetical)
        List<String> predefinedSupplierOrder = List.of(
                "ORDERED\nSMITH DRUGS-O", "ORDERED\nKINRAY-O",
                "ORDERED\nLEGACY HEALTH-O", "ORDERED\nALPINE HEALTH-O",
                "ORDERED\nAKRON GENERICS-O");
        List<String> supplierCols = new ArrayList<>();
        for (Map<String, Object> row : report) {
            for (String k : row.keySet()) {
                if (k.startsWith("ORDERED\n") && k.endsWith("-O") && !supplierCols.contains(k)) {
                    supplierCols.add(k);
                }
            }
        }
        supplierCols.sort((a, b) -> {
            int ia = predefinedSupplierOrder.indexOf(a);
            int ib = predefinedSupplierOrder.indexOf(b);
            if (ia >= 0 && ib >= 0) return Integer.compare(ia, ib);
            if (ia >= 0) return -1;
            if (ib >= 0) return 1;
            return a.compareTo(b);
        });

        List<String> finalColumns = new ArrayList<>();
        finalColumns.addAll(baseColumns);
        finalColumns.addAll(insColumns);
        finalColumns.addAll(supplierCols);
        finalColumns.addAll(cashColumns);
        finalColumns.add("medicine_key");

        // CSV export: legacy has 27 columns (no medicine_key). Omit for file download parity.
        List<String> csvColumns = new ArrayList<>(finalColumns);
        csvColumns.remove("medicine_key");

        // --- 16. Apply zero→blank for numeric columns, write CSV ---
        List<Map<String, Object>> cleanedReport = new ArrayList<>();
        for (Map<String, Object> row : report) {
            Map<String, Object> clean = new LinkedHashMap<>();
            for (String col : finalColumns) {
                Object val = row.get(col);
                if (val == null) {
                    clean.put(col, "");
                } else if (val instanceof Number num) {
                    if ("AMOUNT".equals(col)) {
                        int intVal = num.intValue();
                        clean.put(col, intVal == 0 ? "" : String.valueOf(intVal));
                    } else if ("COST".equals(col)) {
                        double d = num.doubleValue();
                        clean.put(col, d == 0.0 ? "" : formatCost(d));
                    } else if (col.startsWith("HIGHEST")) {
                        // HIGHEST SHORTAGE-S: null → blank (already handled above); if present keep value
                        clean.put(col, formatNum(num.doubleValue()));
                    } else {
                        double d = num.doubleValue();
                        clean.put(col, d == 0.0 ? "" : formatNum(d));
                    }
                } else {
                    clean.put(col, String.valueOf(val));
                }
            }
            cleanedReport.add(clean);
        }

        // Write CSV (27 columns, no medicine_key, for legacy parity)
        Files.createDirectories(outputCsv.getParent());
        try (CSVWriter w = new CSVWriter(
                new OutputStreamWriter(Files.newOutputStream(outputCsv), StandardCharsets.UTF_8))) {
            w.writeNext(csvColumns.toArray(new String[0]));
            for (Map<String, Object> row : cleanedReport) {
                String[] vals = new String[csvColumns.size()];
                for (int i = 0; i < csvColumns.size(); i++) {
                    Object v = row.get(csvColumns.get(i));
                    vals[i] = v == null ? "" : String.valueOf(v);
                }
                w.writeNext(vals);
            }
        }

        // Clean internal fields from returned report (for JSON API response)
        for (Map<String, Object> row : cleanedReport) {
            row.remove("ordered_total_raw");
            row.remove("sold_total_raw");
            row.remove("shortage_qty_raw");
        }

        return cleanedReport;
    }

    // ---- Helper methods ----

    private static void writeEmpty(Path outputCsv) throws IOException {
        // Legacy parity: 27 columns, no medicine_key in CSV
        List<String> headers = List.of(
                "NDC", "DRUG NAME", "RANK", "PKG SIZE",
                "TOTAL\nORDERED-O", "TOTAL\nBILLED-B", "TOTAL\nSHORTAGE-S",
                "HIGHEST\nSHORTAGE-S", "AMOUNT", "COST");
        Files.createDirectories(outputCsv.getParent());
        try (CSVWriter w = new CSVWriter(
                new OutputStreamWriter(Files.newOutputStream(outputCsv), StandardCharsets.UTF_8))) {
            w.writeNext(headers.toArray(new String[0]));
        }
    }

    /** Detect cost field from ordered data (first row with a cost-like column). */
    private static String detectCostField(List<Map<String, Object>> orderedNormalized) {
        if (orderedNormalized.isEmpty()) return null;
        Set<String> cols = orderedNormalized.get(0).keySet();
        for (String candidate : List.of("cost", "unit_cost", "price", "unit_price",
                "total_cost", "extended_cost", "amount", "total_amount")) {
            if (cols.contains(candidate)) return candidate;
        }
        return null;
    }

    private static void addIfPresent(Set<String> set, Map<String, Object> m, String field) {
        String v = str(m.get(field));
        if (!v.isEmpty()) set.add(v);
    }

    /**
     * Normalize insurance name for column headers to match Python/legacy (dawairx_format.py insurance_name_map).
     */
    private static String normalizeInsuranceName(String name) {
        if (name == null || name.isEmpty()) return name;
        String n = name.strip();
        // Exact and case-insensitive mappings to legacy display names
        if (n.equalsIgnoreCase("SS&C (FORMERLY HUMANA ARGUS AND OPTUMRX)")
                || n.equalsIgnoreCase("SS&C (FORMERLY HUMANA, ARGUS, AND OPTUMRX)")
                || n.equalsIgnoreCase("ss&c (formerly humana argus and optumrx)")) {
            return "SS&C (FORMERLY HUMANA, ARGUS, AND DST)";
        }
        if (n.equalsIgnoreCase("cvs caremark")) return "CVS CAREMARK";
        if (n.equalsIgnoreCase("express scripts")) return "EXPRESS SCRIPTS";
        if (n.equalsIgnoreCase("horizon health")) return "HORIZON HEALTH";
        if (n.equalsIgnoreCase("nj medicaid")) return "NJ MEDICAID";
        if (n.equalsIgnoreCase("cash")) return "CASH";
        return n;
    }

    private static String str(Object o) {
        if (o == null) return "";
        String s = String.valueOf(o).trim();
        if ("null".equalsIgnoreCase(s) || "nan".equalsIgnoreCase(s)) return "";
        return s;
    }

    private static double dbl(Object o) {
        if (o == null) return 0;
        if (o instanceof Number n) return n.doubleValue();
        String s = String.valueOf(o).trim().replace(",", "");
        if (s.isEmpty()) return 0;
        try {
            return Double.parseDouble(s);
        } catch (NumberFormatException e) {
            return 0;
        }
    }

    private static String formatNum(double d) {
        if (d == (long) d) return String.valueOf((long) d);
        return String.format(Locale.ROOT, "%.2f", d);
    }

    private static String formatCost(double d) {
        if (d == (long) d) return String.valueOf((long) d);
        return String.format(Locale.ROOT, "%.2f", d);
    }
}
