package com.dawai.reporting;

import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

/**
 * Builds the audit report Excel workbook.
 * Must match Python: src/reporting/excel.py  create_audit_report()
 *
 * Sheets:
 *  1. Inventory Report – DawaiRx format data (0→blank, header styling)
 *  2. Summary – totals and percentages
 *  3. Issues – validation issues
 */
public class ExcelReportBuilder {

    /**
     * @param outputPath      path to .xlsx file
     * @param dawairxReport   report rows (from DawairxReportBuilder, with string values and blanks)
     * @param dawairxColumns  ordered column names (may include \n)
     * @param summary         summary statistics map
     * @param issues          list of issue maps (rule_id, severity, details, ...)
     */
    public static void write(
            Path outputPath,
            List<Map<String, Object>> dawairxReport,
            List<String> dawairxColumns,
            Map<String, Object> summary,
            List<Map<String, Object>> issues
    ) throws IOException {
        Files.createDirectories(outputPath.getParent());

        try (XSSFWorkbook wb = new XSSFWorkbook()) {
            // ---- Sheet 1: Inventory Report ----
            Sheet invSheet = wb.createSheet("Inventory Report");
            writeInventorySheet(wb, invSheet, dawairxReport, dawairxColumns);

            // ---- Sheet 2: Summary ----
            Sheet sumSheet = wb.createSheet("Summary");
            writeSummarySheet(wb, sumSheet, summary);

            // ---- Sheet 3: Issues ----
            Sheet issSheet = wb.createSheet("Issues");
            writeIssuesSheet(wb, issSheet, issues);

            try (FileOutputStream fos = new FileOutputStream(outputPath.toFile())) {
                wb.write(fos);
            }
        }
    }

    private static void writeInventorySheet(Workbook wb, Sheet sheet,
                                            List<Map<String, Object>> rows, List<String> columns) {
        // Header style: blue bg (#366092), white bold text
        CellStyle headerStyle = wb.createCellStyle();
        Font headerFont = wb.createFont();
        headerFont.setBold(true);
        headerFont.setColor(IndexedColors.WHITE.getIndex());
        headerStyle.setFont(headerFont);
        headerStyle.setFillForegroundColor(IndexedColors.DARK_BLUE.getIndex());
        headerStyle.setFillPattern(FillPatternType.SOLID_FOREGROUND);
        headerStyle.setAlignment(HorizontalAlignment.CENTER);

        // Numeric cell style
        CellStyle numStyle = wb.createCellStyle();
        numStyle.setAlignment(HorizontalAlignment.RIGHT);

        // Shortage red style
        CellStyle shortageStyle = wb.createCellStyle();
        Font redFont = wb.createFont();
        redFont.setColor(IndexedColors.RED.getIndex());
        shortageStyle.setFont(redFont);
        shortageStyle.setAlignment(HorizontalAlignment.RIGHT);

        // Write header row
        Row headerRow = sheet.createRow(0);
        for (int i = 0; i < columns.size(); i++) {
            Cell cell = headerRow.createCell(i);
            // Replace \n with space for Excel column header
            cell.setCellValue(columns.get(i).replace("\n", " "));
            cell.setCellStyle(headerStyle);
        }

        // Write data rows
        for (int r = 0; r < rows.size(); r++) {
            Row row = sheet.createRow(r + 1);
            Map<String, Object> data = rows.get(r);
            for (int c = 0; c < columns.size(); c++) {
                String colName = columns.get(c);
                Object val = data.get(colName);
                Cell cell = row.createCell(c);
                if (val == null || "".equals(val)) {
                    cell.setBlank();
                } else {
                    String sv = String.valueOf(val);
                    try {
                        double d = Double.parseDouble(sv);
                        cell.setCellValue(d);
                        // Use red for shortage columns with negative values
                        if (colName.toUpperCase().contains("SHORTAGE") && d < 0) {
                            cell.setCellStyle(shortageStyle);
                        } else {
                            cell.setCellStyle(numStyle);
                        }
                    } catch (NumberFormatException e) {
                        cell.setCellValue(sv);
                    }
                }
            }
        }

        // Auto-size columns (capped at 40 chars)
        for (int i = 0; i < columns.size(); i++) {
            sheet.autoSizeColumn(i);
            int w = sheet.getColumnWidth(i);
            if (w > 40 * 256) sheet.setColumnWidth(i, 40 * 256);
        }
    }

    private static void writeSummarySheet(Workbook wb, Sheet sheet, Map<String, Object> summary) {
        CellStyle headerStyle = wb.createCellStyle();
        Font hf = wb.createFont();
        hf.setBold(true);
        headerStyle.setFont(hf);

        String[][] metrics = {
                {"Total Medicines", "total_medicines"},
                {"Total Ordered", "total_ordered"},
                {"Total Sold", "total_sold"},
                {"Total Remaining", "total_remaining"},
                {"Total Shortage", "total_shortage"},
                {"Total Leftover", "total_leftover"},
                {"Medicines with Shortage", "medicines_with_shortage"},
                {"Medicines with Leftover", "medicines_with_leftover"},
                {"Sold Percentage", "sold_percentage"},
                {"Total Issues", "total_issues"},
        };

        Row headerRow = sheet.createRow(0);
        Cell h0 = headerRow.createCell(0);
        h0.setCellValue("Metric");
        h0.setCellStyle(headerStyle);
        Cell h1 = headerRow.createCell(1);
        h1.setCellValue("Value");
        h1.setCellStyle(headerStyle);

        for (int i = 0; i < metrics.length; i++) {
            Row row = sheet.createRow(i + 1);
            row.createCell(0).setCellValue(metrics[i][0]);
            Object val = summary != null ? summary.get(metrics[i][1]) : null;
            if (val instanceof Number n) {
                row.createCell(1).setCellValue(n.doubleValue());
            } else if (val != null) {
                row.createCell(1).setCellValue(String.valueOf(val));
            }
        }

        sheet.autoSizeColumn(0);
        sheet.autoSizeColumn(1);
    }

    private static void writeIssuesSheet(Workbook wb, Sheet sheet, List<Map<String, Object>> issues) {
        CellStyle headerStyle = wb.createCellStyle();
        Font hf = wb.createFont();
        hf.setBold(true);
        headerStyle.setFont(hf);

        String[] cols = {"rule_id", "severity", "medicine_key", "details"};
        Row headerRow = sheet.createRow(0);
        for (int i = 0; i < cols.length; i++) {
            Cell c = headerRow.createCell(i);
            c.setCellValue(cols[i]);
            c.setCellStyle(headerStyle);
        }

        if (issues != null) {
            for (int r = 0; r < issues.size(); r++) {
                Row row = sheet.createRow(r + 1);
                Map<String, Object> issue = issues.get(r);
                for (int c = 0; c < cols.length; c++) {
                    Object val = issue.get(cols[c]);
                    row.createCell(c).setCellValue(val != null ? String.valueOf(val) : "");
                }
            }
        }

        for (int i = 0; i < cols.length; i++) {
            sheet.autoSizeColumn(i);
        }
    }
}
