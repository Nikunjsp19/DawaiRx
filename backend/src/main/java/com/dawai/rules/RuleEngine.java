package com.dawai.rules;

import com.dawai.normalization.NdcNormalizer;
import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class RuleEngine {

    public List<Map<String, Object>> runAll(
            List<Map<String, Object>> ordered,
            List<Map<String, Object>> sold,
            List<Map<String, Object>> reconciled
    ) {
        List<Map<String, Object>> issues = new ArrayList<>();

        // R002: Invalid NDC
        for (Map<String, Object> row : ordered) {
            Object ndc = row.get("ndc");
            if (ndc != null && !String.valueOf(ndc).isBlank()) {
                if (NdcNormalizer.normalize(String.valueOf(ndc)) == null) {
                    issues.add(createIssue("R002", "high", row.get("medicine_key"),
                            "Invalid NDC format: '" + ndc + "' (must be 10 or 11 digits)",
                            Map.of("source", "ordered"), Map.of("ndc", ndc)));
                }
            }
        }
        for (Map<String, Object> row : sold) {
            Object ndc = row.get("ndc");
            if (ndc != null && !String.valueOf(ndc).isBlank()) {
                if (NdcNormalizer.normalize(String.valueOf(ndc)) == null) {
                    issues.add(createIssue("R002", "high", row.get("medicine_key"),
                            "Invalid NDC format: '" + ndc + "' (must be 10 or 11 digits)",
                            Map.of("source", "sold"), Map.of("ndc", ndc)));
                }
            }
        }

        // R003: Sold not in ordered
        for (Map<String, Object> row : reconciled) {
            double orderedTotal = getDouble(row, "ordered_total");
            double soldTotal = getDouble(row, "sold_total");
            if (orderedTotal == 0 && soldTotal > 0) {
                issues.add(createIssue("R003", "high", row.get("medicine_key"),
                        "Medicine sold but not found in ordered set: " + row.get("drug_name") + " (sold_qty=" + soldTotal + ")",
                        Map.of(), Map.of("sold_total", soldTotal)));
            }
        }

        // R005: Over-sold
        for (Map<String, Object> row : reconciled) {
            double shortage = getDouble(row, "shortage_qty");
            if (shortage > 0) {
                issues.add(createIssue("R005", "high", row.get("medicine_key"),
                        "Over-sold: sold " + getDouble(row, "sold_total") + " but only " + getDouble(row, "ordered_total") + " ordered (shortage: " + shortage + ")",
                        Map.of(), Map.of(
                                "ordered_total", getDouble(row, "ordered_total"),
                                "sold_total", getDouble(row, "sold_total"),
                                "shortage_qty", shortage
                        )));
            }
        }

        return issues;
    }

    private Map<String, Object> createIssue(String ruleId, String severity, Object medicineKey,
                                            String details, Map<String, Object> rowRef, Map<String, Object> rawSnippet) {
        Map<String, Object> issue = new HashMap<>();
        issue.put("rule_id", ruleId);
        issue.put("severity", severity);
        issue.put("medicine_key", medicineKey);
        issue.put("details", details);
        issue.put("row_ref", rowRef);
        issue.put("raw_snippet", rawSnippet);
        return issue;
    }

    private double getDouble(Map<String, Object> m, String key) {
        Object v = m.get(key);
        if (v instanceof Number n) return n.doubleValue();
        if (v == null) return 0;
        try {
            return Double.parseDouble(String.valueOf(v));
        } catch (NumberFormatException e) {
            return 0;
        }
    }
}
