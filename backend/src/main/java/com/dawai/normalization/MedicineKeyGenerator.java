package com.dawai.normalization;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Generates medicine keys for grouping medications.
 * Must match Python: src/normalization/medicine_key.py
 *
 * Strategy:
 *  1. If NDC normalizes to 11 digits → "NDC:{11digits}"
 *  2. Fallback composite → "COMPOSITE:{DRUG_NAME}|{STRENGTH}|{MANUFACTURER}"
 *     where each part is UPPERCASE, multiple-spaces collapsed to single space.
 *  3. Last resort → "UNKNOWN"
 */
public class MedicineKeyGenerator {

    public static String generate(String ndc, String drugName, String strength, String manufacturer) {
        String normalizedNdc = NdcNormalizer.normalize(ndc);
        if (normalizedNdc != null) {
            return "NDC:" + normalizedNdc;
        }

        List<String> parts = new ArrayList<>();
        String n;
        n = normalizeTextForKey(drugName);
        if (n != null) parts.add(n);
        n = normalizeTextForKey(strength);
        if (n != null) parts.add(n);
        n = normalizeTextForKey(manufacturer);
        if (n != null) parts.add(n);

        if (!parts.isEmpty()) {
            return "COMPOSITE:" + String.join("|", parts);
        }
        return "UNKNOWN";
    }

    /**
     * Matches Python normalize_text(text, case="upper"):
     *  - strip whitespace
     *  - reject null-like values ("nan","none","null","")
     *  - collapse multiple spaces to single space
     *  - UPPERCASE
     */
    static String normalizeTextForKey(String s) {
        if (s == null) return null;
        String t = s.trim();
        if (t.isEmpty()) return null;
        String lower = t.toLowerCase(Locale.ROOT);
        if ("nan".equals(lower) || "none".equals(lower) || "null".equals(lower)) return null;
        // collapse whitespace, uppercase
        t = t.replaceAll("\\s+", " ").toUpperCase(Locale.ROOT);
        return t;
    }
}
