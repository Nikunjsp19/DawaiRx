package com.dawai.ingestion;

import com.opencsv.CSVReader;
import com.opencsv.CSVReaderBuilder;
import com.opencsv.exceptions.CsvException;
import org.apache.poi.ss.usermodel.*;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;
import org.springframework.stereotype.Component;

import java.io.*;
import java.nio.file.Path;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.*;

@Component
public class FileLoader {

    public List<Map<String, String>> loadFile(Path filePath) throws IOException {
        String fileName = filePath.getFileName().toString().toLowerCase();
        if (fileName.endsWith(".csv")) {
            return loadCsv(filePath);
        } else if (fileName.endsWith(".xlsx") || fileName.endsWith(".xls")) {
            return loadExcel(filePath);
        } else {
            throw new IllegalArgumentException("Unsupported file type. Use .csv or .xlsx");
        }
    }

    private List<Map<String, String>> loadCsv(Path filePath) throws IOException {
        try {
            return doLoadCsv(filePath);
        } catch (CsvException e) {
            throw new IOException("Failed to parse CSV: " + e.getMessage());
        }
    }

    private List<Map<String, String>> doLoadCsv(Path filePath) throws IOException, CsvException {
        List<Map<String, String>> rows = new ArrayList<>();
        try (Reader reader = new FileReader(filePath.toFile());
             CSVReader csvReader = new CSVReaderBuilder(reader)
                     .withSkipLines(0)
                     .build()) {

            List<String[]> allRows = csvReader.readAll();
            if (allRows.isEmpty()) return rows;

            String[] headers = allRows.get(0);
            for (int i = 1; i < allRows.size(); i++) {
                Map<String, String> row = new HashMap<>();
                String[] values = allRows.get(i);
                for (int j = 0; j < headers.length; j++) {
                    String value = j < values.length ? (values[j] != null ? values[j].trim() : "") : "";
                    row.put(headers[j].trim(), value);
                }
                rows.add(row);
            }
        }
        return rows;
    }

    private List<Map<String, String>> loadExcel(Path filePath) throws IOException {
        List<Map<String, String>> rows = new ArrayList<>();
        try (FileInputStream fis = new FileInputStream(filePath.toFile());
             Workbook workbook = new XSSFWorkbook(fis)) {

            Sheet sheet = workbook.getSheetAt(0);
            Iterator<Row> rowIterator = sheet.iterator();

            if (!rowIterator.hasNext()) return rows;

            Row headerRow = rowIterator.next();
            List<String> headers = new ArrayList<>();
            for (Cell cell : headerRow) {
                headers.add(getCellValue(cell));
            }

            while (rowIterator.hasNext()) {
                Row row = rowIterator.next();
                Map<String, String> rowData = new HashMap<>();
                for (int i = 0; i < headers.size(); i++) {
                    Cell cell = row.getCell(i);
                    rowData.put(headers.get(i), cell != null ? getCellValue(cell) : "");
                }
                rows.add(rowData);
            }
        }
        return rows;
    }

    private String getCellValue(Cell cell) {
        if (cell == null) return "";
        return switch (cell.getCellType()) {
            case STRING -> cell.getStringCellValue();
            case NUMERIC -> {
                double numVal = cell.getNumericCellValue();
                if (DateUtil.isCellDateFormatted(cell)) {
                    try {
                        java.util.Date d = DateUtil.getJavaDate(numVal);
                        yield d != null
                                ? DateTimeFormatter.ISO_LOCAL_DATE.format(
                                        Instant.ofEpochMilli(d.getTime()).atZone(ZoneId.systemDefault()).toLocalDate())
                                : "";
                    } catch (Throwable e) {
                        yield (numVal == (long) numVal) ? String.valueOf((long) numVal) : String.valueOf(numVal);
                    }
                } else {
                    yield (numVal == (long) numVal) ? String.valueOf((long) numVal) : String.valueOf(numVal);
                }
            }
            case BOOLEAN -> String.valueOf(cell.getBooleanCellValue());
            case FORMULA -> cell.getCellFormula();
            default -> "";
        };
    }
}
