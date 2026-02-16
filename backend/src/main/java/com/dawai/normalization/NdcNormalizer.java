package com.dawai.normalization;

import java.util.regex.Pattern;

public class NdcNormalizer {

    private static final Pattern NON_DIGIT = Pattern.compile("\\D");

    public static String normalize(String ndc) {
        if (ndc == null || ndc.isBlank() || "nan".equalsIgnoreCase(ndc) || "none".equalsIgnoreCase(ndc)) {
            return null;
        }
        String digits = NON_DIGIT.matcher(ndc.trim()).replaceAll("");
        if (digits.length() < 10 || digits.length() > 11) return null;
        if (digits.length() == 10) {
            return digits.substring(0, 5) + digits.substring(5, 9) + "0" + digits.substring(9);
        }
        return digits;
    }

    /** Format 11-digit NDC for display (5-4-2), e.g. "12345-6789-01". */
    public static String formatDisplay(String ndc) {
        if (ndc == null || ndc.isBlank()) return ndc;
        String digits = NON_DIGIT.matcher(ndc.trim()).replaceAll("");
        if (digits.length() != 11) return ndc;
        return digits.substring(0, 5) + "-" + digits.substring(5, 9) + "-" + digits.substring(9);
    }
}
