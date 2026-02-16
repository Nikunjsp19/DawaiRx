package com.dawai.ingestion;

import org.springframework.stereotype.Component;

import java.util.*;
import java.util.regex.Pattern;

@Component
public class ColumnMapper {

    private static final Map<String, List<String>> CANONICAL_FIELDS = new HashMap<>(Map.ofEntries(
            Map.entry("drug_name", List.of("drug_name", "drug", "medication", "med_name", "product_name", "drug name", "drugname", "item_description", "itemdescription")),
            Map.entry("ndc", List.of("ndc", "ndc_code", "ndc11", "ndc_11", "national_drug_code", "ndc number", "ndcnumber", "ndc_number")),
            Map.entry("strength", List.of("strength", "dosage", "dose", "dosage_strength")),
            Map.entry("manufacturer", List.of("manufacturer", "mfr", "maker", "manufacturer_name")),
            Map.entry("quantity", List.of("quantity", "qty", "qty_dispensed", "quantity_dispensed", "amount", "qty_disp", "dispensed_qty")),
            Map.entry("ordered_qty", List.of("ordered_qty", "ordered_quantity", "qty_ordered", "order_qty", "ordered qty", "orderedqty")),
            Map.entry("sold_qty", List.of("sold_qty", "sold_quantity", "qty_sold", "sold", "quantity", "qty", "qty_dispensed", "quantity_dispensed")),
            Map.entry("rx_number", List.of("rx_number", "rx_num", "prescription_number", "rx_no", "rx number", "rxnumber")),
            Map.entry("fill_number", List.of("fill_number", "fill_num", "fill_no", "fill number", "fillnumber")),
            Map.entry("claim_date", List.of("claim_date", "date", "fill_date", "dispense_date", "transaction_date", "date filled", "datefilled", "date_filled", "fill date", "dispense date")),
            Map.entry("order_date", List.of("order_date", "ordered_date", "invoice_date", "invoice date", "order date", "purchase_date", "purchase date")),
            Map.entry("days_supply", List.of("days_supply", "days", "supply_days", "days supply")),
            Map.entry("pkg_size", List.of("pkg_size", "pkg size", "package_size", "package size", "PKG SIZE", "qty_per_package")),
            Map.entry("supplier_name", List.of("supplier_name", "supplier name", "supplier", "vendor", "distributor")),
            Map.entry("primary_insurance_paid", List.of("primary_insurance_paid", "primary insurance paid", "primary_paid", "insurance_paid")),
            Map.entry("secondary_insurance_paid", List.of("secondary_insurance_paid", "secondary insurance paid", "secondary_paid")),
            Map.entry("primary_insurance_name", List.of("primary_insurance_name", "primary insurance", "primary_insurance", "insurance")),
            Map.entry("secondary_insurance_name", List.of("secondary_insurance_name", "secondary insurance", "secondary_insurance"))
    ));

    public static final Set<String> REQUIRED_ORDERED = Set.of("drug_name", "ndc", "ordered_qty");
    public static final Set<String> REQUIRED_SOLD = Set.of("drug_name", "ndc", "sold_qty");

    private static final Pattern NON_WORD = Pattern.compile("[^\\w]");
    private static final Pattern MULTI_UNDERSCORE = Pattern.compile("_+");

    public Map<String, String> createMapping(Collection<String> columns, String reportType) {
        Map<String, String> mapping = new HashMap<>();
        for (String col : columns) {
            String canonical = guessCanonical(col);
            if (canonical != null) {
                if ("quantity".equals(canonical)) {
                    canonical = "ordered".equals(reportType) ? "ordered_qty" : "sold_qty";
                }
                mapping.put(col, canonical);
            }
        }
        return mapping;
    }

    public List<Map<String, String>> applyMapping(List<Map<String, String>> rows, Map<String, String> mapping) {
        if (rows.isEmpty() || mapping.isEmpty()) return rows;

        List<Map<String, String>> result = new ArrayList<>();
        for (Map<String, String> row : rows) {
            Map<String, String> newRow = new HashMap<>();
            for (Map.Entry<String, String> entry : row.entrySet()) {
                String canonical = mapping.get(entry.getKey());
                if (canonical != null) {
                    newRow.put(canonical, entry.getValue());
                } else {
                    newRow.put(entry.getKey(), entry.getValue());
                }
            }
            result.add(newRow);
        }
        return result;
    }

    private String guessCanonical(String columnName) {
        String normalized = normalizeColumnName(columnName);

        for (Map.Entry<String, List<String>> entry : CANONICAL_FIELDS.entrySet()) {
            String canonical = entry.getKey();
            for (String variant : entry.getValue()) {
                if (normalized.equals(normalizeColumnName(variant))) {
                    return canonical;
                }
            }
            if (normalized.equals(normalizeColumnName(canonical))) {
                return canonical;
            }
        }

        if (normalized.contains("ndc") && (normalized.contains("number") || normalized.contains("code"))) return "ndc";
        if (normalized.contains("drug") && normalized.contains("name")) return "drug_name";
        if (normalized.contains("item") && normalized.contains("description")) return "drug_name";
        if (normalized.contains("date") && normalized.contains("filled")) return "claim_date";
        if (Set.of("quantity", "qty", "qty_dispensed", "quantity_dispensed").contains(normalized)) return "quantity";

        return null;
    }

    private String normalizeColumnName(String col) {
        String s = NON_WORD.matcher(col.toLowerCase().trim()).replaceAll("_");
        return MULTI_UNDERSCORE.matcher(s).replaceAll("_");
    }
}
