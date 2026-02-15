package com.dawai.normalization;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for NormalizationService matching Python: src/normalization/processor.py
 */
class NormalizationServiceTest {

    private final NormalizationService svc = new NormalizationService();

    @Test
    void normalize_orderedRow_textUpperCase() {
        Map<String, String> row = Map.of(
                "ndc", "12345-6789-01",
                "drug_name", "aspirin delayed release",
                "strength", "81mg",
                "manufacturer", "bayer corp",
                "ordered_qty", "100"
        );
        List<Map<String, Object>> result = svc.normalize(List.of(row), "ordered");
        assertEquals(1, result.size());
        Map<String, Object> r = result.get(0);
        assertEquals("12345678901", r.get("ndc"));
        assertEquals("ASPIRIN DELAYED RELEASE", r.get("drug_name"));
        assertEquals("81MG", r.get("strength"));
        assertEquals("BAYER CORP", r.get("manufacturer"));
        assertEquals(100.0, (Double) r.get("ordered_qty"), 0.001);
        assertEquals("NDC:12345678901", r.get("medicine_key"));
    }

    @Test
    void normalize_preservesOriginals() {
        Map<String, String> row = Map.of(
                "ndc", "12345-6789-01",
                "drug_name", "Aspirin Tab",
                "ordered_qty", "50"
        );
        List<Map<String, Object>> result = svc.normalize(List.of(row), "ordered");
        Map<String, Object> r = result.get(0);
        assertEquals("Aspirin Tab", r.get("drug_name_original"));
        assertEquals("12345-6789-01", r.get("ndc_original"));
    }

    @Test
    void normalize_soldRow_quantityField() {
        Map<String, String> row = Map.of(
                "ndc", "98765-4321-0",
                "drug_name", "metformin",
                "sold_qty", "30"
        );
        List<Map<String, Object>> result = svc.normalize(List.of(row), "sold");
        Map<String, Object> r = result.get(0);
        assertEquals(30.0, (Double) r.get("sold_qty"), 0.001);
    }

    @Test
    void normalize_dateField() {
        Map<String, String> row = Map.of(
                "ndc", "12345678901",
                "drug_name", "Aspirin",
                "sold_qty", "10",
                "claim_date", "12/15/2025"
        );
        List<Map<String, Object>> result = svc.normalize(List.of(row), "sold");
        Map<String, Object> r = result.get(0);
        assertEquals("2025-12-15", r.get("claim_date"));
    }

    @Test
    void normalize_quantityWithCommas() {
        Map<String, String> row = Map.of(
                "drug_name", "Test",
                "ordered_qty", "1,500"
        );
        List<Map<String, Object>> result = svc.normalize(List.of(row), "ordered");
        assertEquals(1500.0, (Double) result.get(0).get("ordered_qty"), 0.001);
    }

    @Test
    void normalize_quantityWithDollarSign() {
        Map<String, String> row = Map.of(
                "drug_name", "Test",
                "ordered_qty", "$25.50"
        );
        List<Map<String, Object>> result = svc.normalize(List.of(row), "ordered");
        assertEquals(25.50, (Double) result.get(0).get("ordered_qty"), 0.001);
    }

    @Test
    void normalize_fallbackQuantityField() {
        // If "ordered_qty" missing but "quantity" present → use "quantity" as ordered_qty
        Map<String, String> row = Map.of(
                "drug_name", "Test",
                "quantity", "42"
        );
        List<Map<String, Object>> result = svc.normalize(List.of(row), "ordered");
        assertEquals(42.0, (Double) result.get(0).get("ordered_qty"), 0.001);
    }

    @Test
    void normalize_medicineKey_compositeWhenNdcInvalid() {
        Map<String, String> row = Map.of(
                "ndc", "BAD",
                "drug_name", "Aspirin",
                "strength", "81MG",
                "manufacturer", "Bayer"
        );
        List<Map<String, Object>> result = svc.normalize(List.of(row), "ordered");
        assertEquals("COMPOSITE:ASPIRIN|81MG|BAYER", result.get(0).get("medicine_key"));
    }

    @Test
    void parseDate_multipleFormats() {
        assertEquals("2025-12-15", NormalizationService.parseDate("2025-12-15"));
        assertEquals("2025-12-15", NormalizationService.parseDate("12/15/2025"));
        assertEquals("2025-01-05", NormalizationService.parseDate("1/5/2025"));
        assertNull(NormalizationService.parseDate("not-a-date"));
        assertNull(NormalizationService.parseDate(null));
        assertNull(NormalizationService.parseDate(""));
    }
}
