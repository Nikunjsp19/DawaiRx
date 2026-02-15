package com.dawai.normalization;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for NDC normalization matching Python: src/normalization/ndc.py
 */
class NdcNormalizerTest {

    @Test
    void nullInput() {
        assertNull(NdcNormalizer.normalize(null));
    }

    @ParameterizedTest
    @CsvSource({
        "'',",
        "'nan',",
        "'none',",
        "'null',",
        "'   ',",
    })
    void blankOrNullLike(String input) {
        assertNull(NdcNormalizer.normalize(input));
    }

    @Test
    void alreadyElevenDigits() {
        assertEquals("12345678901", NdcNormalizer.normalize("12345678901"));
    }

    @Test
    void tenDigitsPaddedTo11() {
        // 10-digit 12345-6789-0 → 5-4-1 → pad package to 2 digits: 12345678900 → no
        // Actually: 1234567890 → labeler=12345, product=6789, package=0 → 12345678900
        assertEquals("12345678900", NdcNormalizer.normalize("1234567890"));
    }

    @Test
    void hyphenatedTenDigit() {
        // 12345-6789-0 → digits=1234567890 → len=10 → pad: 12345678900
        assertEquals("12345678900", NdcNormalizer.normalize("12345-6789-0"));
    }

    @Test
    void hyphenatedElevenDigit() {
        assertEquals("12345678901", NdcNormalizer.normalize("12345-6789-01"));
    }

    @Test
    void spaceSeparated() {
        assertEquals("12345678901", NdcNormalizer.normalize("12345 6789 01"));
    }

    @Test
    void tooShort() {
        assertNull(NdcNormalizer.normalize("123456789")); // 9 digits
    }

    @Test
    void tooLong() {
        assertNull(NdcNormalizer.normalize("123456789012")); // 12 digits
    }

    @Test
    void formatDisplay() {
        assertEquals("12345-6789-01", NdcNormalizer.formatDisplay("12345678901"));
    }

    @Test
    void formatDisplayInvalid() {
        // Non-11-digit returns as-is
        assertEquals("1234", NdcNormalizer.formatDisplay("1234"));
    }

    @Test
    void realWorldNdc_98765_4321_0() {
        // 98765-4321-0 → digits=9876543210 → 10 digits → pad: 98765432100
        assertEquals("98765432100", NdcNormalizer.normalize("98765-4321-0"));
    }

    @Test
    void realWorldNdc_55555_1111_22() {
        assertEquals("55555111122", NdcNormalizer.normalize("55555-1111-22"));
    }
}
