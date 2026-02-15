# Legacy (Python) vs New (Java) Report Parity Diff

- **Legacy:** `Report_20250114_to_20260206.csv`
- **New:** `download (3).csv`

## 1. Summary counts

| Metric | Legacy | New |
|--------|--------|-----|
| Rows | 54 | 54 |
| Columns (normalized) | 27 | 27 |
| Common row keys | | 54 |
| Rows only in legacy | 0 |
| Rows only in new | 0 |
| Cell-level mismatches | | 73 |

## 2. Column differences

- **Missing in new (expected in legacy):** None
- **Extra in new:** None (medicine_key is intentional)

## 3. Row differences

## 4. Mismatch counts by column (before/after parity)

| Column | Mismatch count |
|--------|----------------|
| RANK | 23 |
| TOTAL ORDERED-O | 10 |
| ORDERED KINRAY-O | 10 |
| HIGHEST SHORTAGE-S | 10 |
| TOTAL SHORTAGE-S | 10 |
| SHORTAGE CVS CAREMARK-S | 4 |
| SHORTAGE EXPRESS SCRIPTS-S | 4 |
| SHORTAGE HORIZON HEALTH-S | 2 |

## 5. Top mismatch categories (by column)

- `RANK`: 23 mismatches
- `TOTAL ORDERED-O`: 10 mismatches
- `ORDERED KINRAY-O`: 10 mismatches
- `HIGHEST SHORTAGE-S`: 10 mismatches
- `TOTAL SHORTAGE-S`: 10 mismatches
- `SHORTAGE CVS CAREMARK-S`: 4 mismatches
- `SHORTAGE EXPRESS SCRIPTS-S`: 4 mismatches
- `SHORTAGE HORIZON HEALTH-S`: 2 mismatches

## 6. Sample cell-level mismatches

| Row identifier | Column | Legacy | New | Delta (if numeric) |
|----------------|--------|--------|-----|---------------------|
| 70377-0007-13|ROSUVASTATIN (U) 10MG TAB | TOTAL ORDERED-O | (blank) | 11000 |  |
| 70377-0007-13|ROSUVASTATIN (U) 10MG TAB | ORDERED KINRAY-O | (blank) | 11000 |  |
| 70377-0007-13|ROSUVASTATIN (U) 10MG TAB | SHORTAGE CVS CAREMARK-S | -0.18 | 10999.82 | 11000.0 |
| 70377-0007-13|ROSUVASTATIN (U) 10MG TAB | HIGHEST SHORTAGE-S | -0.18 | (blank) |  |
| 70377-0007-13|ROSUVASTATIN (U) 10MG TAB | TOTAL SHORTAGE-S | -0.18 | 10999.82 | 11000.0 |
| 72578-0100-92|LEVOFLOXACIN 750MG TAB | RANK | 52 | 49 | -3.0 |
| 00536-1294-97|DICLOFENAC SODIUM(U) 1% GE | TOTAL ORDERED-O | (blank) | 1500 |  |
| 00536-1294-97|DICLOFENAC SODIUM(U) 1% GE | ORDERED KINRAY-O | (blank) | 1500 |  |
| 00536-1294-97|DICLOFENAC SODIUM(U) 1% GE | HIGHEST SHORTAGE-S | -1.0 | (blank) |  |
| 00536-1294-97|DICLOFENAC SODIUM(U) 1% GE | SHORTAGE HORIZON HEALTH-S | -1.0 | 1499 | 1500.0 |
| 00536-1294-97|DICLOFENAC SODIUM(U) 1% GE | TOTAL SHORTAGE-S | -1.0 | 1499 | 1500.0 |
| 68180-0513-03|LISINOPRIL (U) 5MG TAB | RANK | 50 | 46 | -4.0 |
| 57896-0921-01|ASPIRIN 325MG TAB | RANK | 48 | 50 | 2.0 |
| 69097-0128-15|AMLODIPINE BESYLATE (U) 10 | RANK | 34 | 33 | -1.0 |
| 00002-1484-80|MOUNJARO 7.5MG/0.5ML INJ | SHORTAGE EXPRESS SCRIPTS-S | -1.0 | 15 | 16.0 |
| 00002-1484-80|MOUNJARO 7.5MG/0.5ML INJ | TOTAL ORDERED-O | (blank) | 16 |  |
| 00002-1484-80|MOUNJARO 7.5MG/0.5ML INJ | ORDERED KINRAY-O | (blank) | 16 |  |
| 00002-1484-80|MOUNJARO 7.5MG/0.5ML INJ | HIGHEST SHORTAGE-S | -1.0 | (blank) |  |
| 00002-1484-80|MOUNJARO 7.5MG/0.5ML INJ | TOTAL SHORTAGE-S | -1.0 | 15 | 16.0 |
| 68180-0980-03|LISINOPRIL (U) 10MG TAB | RANK | 43 | 41 | -2.0 |
| 65862-0560-99|PANTOPRAZOLE (U) 40MG TAB | TOTAL ORDERED-O | (blank) | 25000 |  |
| 65862-0560-99|PANTOPRAZOLE (U) 40MG TAB | ORDERED KINRAY-O | (blank) | 25000 |  |
| 65862-0560-99|PANTOPRAZOLE (U) 40MG TAB | SHORTAGE CVS CAREMARK-S | -0.03 | 24999.97 | 25000.0 |
| 65862-0560-99|PANTOPRAZOLE (U) 40MG TAB | HIGHEST SHORTAGE-S | -0.03 | (blank) |  |
| 65862-0560-99|PANTOPRAZOLE (U) 40MG TAB | TOTAL SHORTAGE-S | -0.03 | 24999.97 | 25000.0 |
| 58657-0164-01|MULTIVIT/FLUOR 0.5MG CHEW | RANK | 33 | 34 | 1.0 |
| 31722-0522-01|HYDRALAZINE HCL(U) 100MG T | TOTAL ORDERED-O | (blank) | 2200 |  |
| 31722-0522-01|HYDRALAZINE HCL(U) 100MG T | ORDERED KINRAY-O | (blank) | 2200 |  |
| 31722-0522-01|HYDRALAZINE HCL(U) 100MG T | SHORTAGE CVS CAREMARK-S | -0.3 | 2199.70 | 2200.0 |
| 31722-0522-01|HYDRALAZINE HCL(U) 100MG T | RANK | 37 | 43 | 6.0 |
| 31722-0522-01|HYDRALAZINE HCL(U) 100MG T | HIGHEST SHORTAGE-S | -0.3 | (blank) |  |
| 31722-0522-01|HYDRALAZINE HCL(U) 100MG T | TOTAL SHORTAGE-S | -0.3 | 2199.70 | 2200.0 |
| 68180-0968-03|LEVOTHYROXINE SODIUM | RANK | 19 | 18 | -1.0 |
| 16103-0361-11|CALCIUM | VITD (OYS) | RANK | 47 | 54 | 7.0 |
| 45802-0465-64|KETOCONAZOLE 2% SHAMPOO | RANK | 27 | 26 | -1.0 |
| 59651-0214-30|AZELASTINE HYDROCHLO | SHORTAGE EXPRESS SCRIPTS-S | -1.0 | 539 | 540.0 |
| 59651-0214-30|AZELASTINE HYDROCHLO | TOTAL ORDERED-O | (blank) | 540 |  |
| 59651-0214-30|AZELASTINE HYDROCHLO | ORDERED KINRAY-O | (blank) | 540 |  |
| 59651-0214-30|AZELASTINE HYDROCHLO | RANK | 23 | 24 | 1.0 |
| 59651-0214-30|AZELASTINE HYDROCHLO | HIGHEST SHORTAGE-S | -1.0 | (blank) |  |
| 59651-0214-30|AZELASTINE HYDROCHLO | TOTAL SHORTAGE-S | -1.0 | 539 | 540.0 |
| 45802-0257-35|MOMETASONE FUROATE 0.1% | RANK | 26 | 27 | 1.0 |
| 68180-0963-01|ALBUTEROL(U) | TOTAL ORDERED-O | (blank) | 85 |  |
| 68180-0963-01|ALBUTEROL(U) | ORDERED KINRAY-O | (blank) | 85 |  |
| 68180-0963-01|ALBUTEROL(U) | HIGHEST SHORTAGE-S | -1.0 | (blank) |  |
| 68180-0963-01|ALBUTEROL(U) | SHORTAGE HORIZON HEALTH-S | -1.0 | 84 | 85.0 |
| 68180-0963-01|ALBUTEROL(U) | TOTAL SHORTAGE-S | -1.0 | 84 | 85.0 |
| 69238-1311-09|PREGABALIN 50MG CAP | SHORTAGE EXPRESS SCRIPTS-S | -0.67 | 1079.33 | 1080.0 |
| 69238-1311-09|PREGABALIN 50MG CAP | TOTAL ORDERED-O | (blank) | 1080 |  |
| 69238-1311-09|PREGABALIN 50MG CAP | ORDERED KINRAY-O | (blank) | 1080 |  |

## 7. Logic notes

- **TOTAL ORDERED-O / TOTAL SHORTAGE-S:** Differences often due to different run inputs (date range or ordered data). Legacy may have had date filter excluding some ordered rows; Java uses same formula: TOTAL SHORTAGE-S = TOTAL ORDERED-O - TOTAL BILLED-B.
- **Insurance column name:** Legacy uses normalized name `SS&C (FORMERLY HUMANA, ARGUS, AND DST)`; new uses raw `SS&C (FORMERLY HUMANA ARGUS AND OPTUMRX)`. Backend should normalize insurance names to match Python.
- **medicine_key:** New CSV includes `medicine_key`; legacy does not. Optional backend change to omit for exact column match.
- **RANK:** Order differs when AMOUNT/COST differ (e.g. blank in legacy vs value in new); sort is AMOUNT desc, COST desc in both.
