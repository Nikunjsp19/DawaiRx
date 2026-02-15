package com.dawai.normalization;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for medicine key generation matching Python: src/normalization/medicine_key.py
 */
class MedicineKeyGeneratorTest {

    @Test
    void ndcBasedKey() {
        // Valid 11-digit NDC → NDC:...
        assertEquals("NDC:12345678901", MedicineKeyGenerator.generate("12345-6789-01", "Aspirin", "81MG", "Bayer"));
    }

    @Test
    void ndcBasedKey_10digit() {
        // Valid 10-digit NDC → padded to 11 → NDC:...
        assertEquals("NDC:12345678900", MedicineKeyGenerator.generate("12345-6789-0", "Aspirin", "81MG", "Bayer"));
    }

    @Test
    void compositeKey_noValidNdc() {
        // Invalid NDC → falls back to COMPOSITE
        String key = MedicineKeyGenerator.generate("BAD", "Aspirin Delayed Release", "81MG", "Bayer Corp");
        assertEquals("COMPOSITE:ASPIRIN DELAYED RELEASE|81MG|BAYER CORP", key);
    }

    @Test
    void compositeKey_nullNdc() {
        String key = MedicineKeyGenerator.generate(null, "metformin hcl", "500mg", "teva");
        assertEquals("COMPOSITE:METFORMIN HCL|500MG|TEVA", key);
    }

    @Test
    void compositeKey_multipleSpaces() {
        // Multiple spaces collapsed to single
        String key = MedicineKeyGenerator.generate(null, "Aspirin  Delayed   Release", "81MG", "Bayer");
        assertEquals("COMPOSITE:ASPIRIN DELAYED RELEASE|81MG|BAYER", key);
    }

    @Test
    void compositeKey_partialFields() {
        // Only drug_name
        String key = MedicineKeyGenerator.generate(null, "Aspirin", null, null);
        assertEquals("COMPOSITE:ASPIRIN", key);
    }

    @Test
    void unknownKey() {
        assertEquals("UNKNOWN", MedicineKeyGenerator.generate(null, null, null, null));
    }

    @Test
    void unknownKey_blankFields() {
        assertEquals("UNKNOWN", MedicineKeyGenerator.generate("", "", "", ""));
    }

    @Test
    void compositeKey_nanNdc() {
        // "nan" NDC → falls back
        String key = MedicineKeyGenerator.generate("nan", "Aspirin", "81MG", "Bayer");
        assertEquals("COMPOSITE:ASPIRIN|81MG|BAYER", key);
    }
}
