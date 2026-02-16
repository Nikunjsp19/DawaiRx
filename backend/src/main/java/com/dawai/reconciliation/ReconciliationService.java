package com.dawai.reconciliation;

import org.springframework.stereotype.Service;

import java.util.*;

@Service
public class ReconciliationService {

    public List<Map<String, Object>> reconcile(
            List<Map<String, Object>> ordered,
            List<Map<String, Object>> sold
    ) {
        Map<String, Map<String, Object>> orderedByKey = aggregateByMedicineKey(ordered, "ordered_qty", "ordered_total");
        Map<String, Map<String, Object>> soldByKey = aggregateByMedicineKey(sold, "sold_qty", "sold_total");

        Set<String> allKeys = new HashSet<>();
        allKeys.addAll(orderedByKey.keySet());
        allKeys.addAll(soldByKey.keySet());

        List<Map<String, Object>> result = new ArrayList<>();
        for (String key : allKeys) {
            Map<String, Object> o = orderedByKey.getOrDefault(key, new HashMap<>());
            Map<String, Object> s = soldByKey.getOrDefault(key, new HashMap<>());

            double orderedTotal = getDouble(o, "ordered_total");
            double soldTotal = getDouble(s, "sold_total");
            double remaining = orderedTotal - soldTotal;
            double shortage = remaining < 0 ? Math.abs(remaining) : 0;
            double leftover = remaining > 0 ? remaining : 0;

            Map<String, Object> row = new HashMap<>();
            row.put("medicine_key", key);
            row.put("drug_name", coalesce(o.get("drug_name"), s.get("drug_name")));
            row.put("strength", coalesce(o.get("strength"), s.get("strength")));
            row.put("manufacturer", coalesce(o.get("manufacturer"), s.get("manufacturer")));
            row.put("ndc", coalesce(o.get("ndc"), s.get("ndc")));
            row.put("ordered_total", orderedTotal);
            row.put("sold_total", soldTotal);
            row.put("remaining_qty", remaining);
            row.put("shortage_qty", shortage);
            row.put("leftover_qty", leftover);
            result.add(row);
        }
        return result;
    }

    public Map<String, Object> generateSummary(List<Map<String, Object>> reconciled) {
        Map<String, Object> summary = new HashMap<>();
        summary.put("total_medicines", reconciled.size());
        double totalOrdered = reconciled.stream().mapToDouble(r -> getDouble(r, "ordered_total")).sum();
        double totalSold = reconciled.stream().mapToDouble(r -> getDouble(r, "sold_total")).sum();
        double totalRemaining = reconciled.stream().mapToDouble(r -> getDouble(r, "remaining_qty")).sum();
        double totalShortage = reconciled.stream().mapToDouble(r -> getDouble(r, "shortage_qty")).sum();
        double totalLeftover = reconciled.stream().mapToDouble(r -> getDouble(r, "leftover_qty")).sum();

        summary.put("total_ordered", totalOrdered);
        summary.put("total_sold", totalSold);
        summary.put("total_remaining", totalRemaining);
        summary.put("total_shortage", totalShortage);
        summary.put("total_leftover", totalLeftover);
        summary.put("medicines_with_shortage", reconciled.stream().filter(r -> getDouble(r, "shortage_qty") > 0).count());
        summary.put("medicines_with_leftover", reconciled.stream().filter(r -> getDouble(r, "leftover_qty") > 0).count());
        summary.put("sold_percentage", totalOrdered > 0 ? (totalSold / totalOrdered) * 100 : 0);

        return summary;
    }

    private Map<String, Map<String, Object>> aggregateByMedicineKey(
            List<Map<String, Object>> rows,
            String qtyField,
            String outputField
    ) {
        Map<String, Map<String, Object>> result = new HashMap<>();
        for (Map<String, Object> row : rows) {
            Object key = row.get("medicine_key");
            if (key == null || "UNKNOWN".equals(key)) continue;
            String k = (String) key;
            result.compute(k, (kk, existing) -> {
                Map<String, Object> m = existing != null ? new HashMap<>(existing) : new HashMap<>();
                m.put("medicine_key", k);
                m.put("drug_name", coalesce(m.get("drug_name"), row.get("drug_name")));
                m.put("strength", coalesce(m.get("strength"), row.get("strength")));
                m.put("manufacturer", coalesce(m.get("manufacturer"), row.get("manufacturer")));
                m.put("ndc", coalesce(m.get("ndc"), row.get("ndc")));
                double qty = getDouble(m, outputField) + getDouble(row, qtyField);
                m.put(outputField, qty);
                return m;
            });
        }
        return result;
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

    private Object coalesce(Object a, Object b) {
        return (a != null && !"".equals(a)) ? a : b;
    }
}
