package com.dawai.reconciliation;

import org.junit.jupiter.api.Test;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for ReconciliationService matching Python: src/reconciliation/engine.py
 */
class ReconciliationServiceTest {

    private final ReconciliationService svc = new ReconciliationService();

    @Test
    void reconcile_basic() {
        List<Map<String, Object>> ordered = List.of(
                row("NDC:11111111111", "Aspirin", 100, "ordered_qty"),
                row("NDC:22222222222", "Metformin", 200, "ordered_qty")
        );
        List<Map<String, Object>> sold = List.of(
                row("NDC:11111111111", "Aspirin", 30, "sold_qty"),
                row("NDC:11111111111", "Aspirin", 20, "sold_qty"),
                row("NDC:22222222222", "Metformin", 250, "sold_qty")
        );
        List<Map<String, Object>> result = svc.reconcile(ordered, sold);
        assertEquals(2, result.size());

        Map<String, Object> aspirin = find(result, "NDC:11111111111");
        assertNotNull(aspirin);
        assertEquals(100.0, dbl(aspirin.get("ordered_total")));
        assertEquals(50.0, dbl(aspirin.get("sold_total")));
        assertEquals(50.0, dbl(aspirin.get("remaining_qty")));
        assertEquals(0.0, dbl(aspirin.get("shortage_qty")));
        assertEquals(50.0, dbl(aspirin.get("leftover_qty")));

        Map<String, Object> metformin = find(result, "NDC:22222222222");
        assertNotNull(metformin);
        assertEquals(200.0, dbl(metformin.get("ordered_total")));
        assertEquals(250.0, dbl(metformin.get("sold_total")));
        assertEquals(-50.0, dbl(metformin.get("remaining_qty")));
        assertEquals(50.0, dbl(metformin.get("shortage_qty")));
        assertEquals(0.0, dbl(metformin.get("leftover_qty")));
    }

    @Test
    void reconcile_soldNotInOrdered() {
        List<Map<String, Object>> ordered = List.of(
                row("NDC:11111111111", "Aspirin", 100, "ordered_qty")
        );
        List<Map<String, Object>> sold = List.of(
                row("NDC:33333333333", "Unknown Drug", 50, "sold_qty")
        );
        List<Map<String, Object>> result = svc.reconcile(ordered, sold);
        assertEquals(2, result.size());

        Map<String, Object> unknown = find(result, "NDC:33333333333");
        assertNotNull(unknown);
        assertEquals(0.0, dbl(unknown.get("ordered_total")));
        assertEquals(50.0, dbl(unknown.get("sold_total")));
        assertEquals(50.0, dbl(unknown.get("shortage_qty")));
    }

    @Test
    void generateSummary_basic() {
        List<Map<String, Object>> reconciled = List.of(
                Map.of("ordered_total", 100.0, "sold_total", 80.0,
                        "remaining_qty", 20.0, "shortage_qty", 0.0, "leftover_qty", 20.0),
                Map.of("ordered_total", 200.0, "sold_total", 250.0,
                        "remaining_qty", -50.0, "shortage_qty", 50.0, "leftover_qty", 0.0)
        );
        Map<String, Object> summary = svc.generateSummary(reconciled);
        assertEquals(2, ((Number) summary.get("total_medicines")).intValue());
        assertEquals(300.0, dbl(summary.get("total_ordered")));
        assertEquals(330.0, dbl(summary.get("total_sold")));
        assertEquals(50.0, dbl(summary.get("total_shortage")));
        assertEquals(20.0, dbl(summary.get("total_leftover")));
    }

    @Test
    void reconcile_emptyInputs() {
        List<Map<String, Object>> result = svc.reconcile(Collections.emptyList(), Collections.emptyList());
        assertTrue(result.isEmpty());
    }

    // ---- helpers ----

    private Map<String, Object> row(String key, String drugName, double qty, String qtyField) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("medicine_key", key);
        m.put("drug_name", drugName);
        m.put(qtyField, qty);
        return m;
    }

    private Map<String, Object> find(List<Map<String, Object>> rows, String key) {
        return rows.stream()
                .filter(r -> key.equals(r.get("medicine_key")))
                .findFirst().orElse(null);
    }

    private double dbl(Object o) {
        if (o instanceof Number n) return n.doubleValue();
        return 0;
    }
}
