package com.dawai.document;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.CompoundIndex;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.util.Map;

@Document(collection = "run_items")
@CompoundIndex(name = "user_run_idx", def = "{'user_id': 1, 'run_id': 1}")
public class RunItemDocument {

    @Id
    private String id;
    @Field("run_id")
    private String runId;
    @Field("user_id")
    private String userId;
    @Field("medicine_key")
    private String medicineKey;
    @Field("drug_name")
    private String drugName;
    private String ndc;
    private String strength;
    private String manufacturer;
    @Field("ordered_qty")
    private double orderedQty;
    @Field("sold_qty")
    private double soldQty;
    @Field("remaining_qty")
    private double remainingQty;
    @Field("shortage_qty")
    private double shortageQty;
    @Field("leftover_qty")
    private double leftoverQty;
    /** Full row data (all columns) as returned by report pipeline or loaded from CSV. When set, API returns this map. */
    @Field("row_data")
    private Map<String, Object> rowData;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getRunId() { return runId; }
    public void setRunId(String runId) { this.runId = runId; }
    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }
    public String getMedicineKey() { return medicineKey; }
    public void setMedicineKey(String medicineKey) { this.medicineKey = medicineKey; }
    public String getDrugName() { return drugName; }
    public void setDrugName(String drugName) { this.drugName = drugName; }
    public String getNdc() { return ndc; }
    public void setNdc(String ndc) { this.ndc = ndc; }
    public String getStrength() { return strength; }
    public void setStrength(String strength) { this.strength = strength; }
    public String getManufacturer() { return manufacturer; }
    public void setManufacturer(String manufacturer) { this.manufacturer = manufacturer; }
    public double getOrderedQty() { return orderedQty; }
    public void setOrderedQty(double orderedQty) { this.orderedQty = orderedQty; }
    public double getSoldQty() { return soldQty; }
    public void setSoldQty(double soldQty) { this.soldQty = soldQty; }
    public double getRemainingQty() { return remainingQty; }
    public void setRemainingQty(double remainingQty) { this.remainingQty = remainingQty; }
    public double getShortageQty() { return shortageQty; }
    public void setShortageQty(double shortageQty) { this.shortageQty = shortageQty; }
    public double getLeftoverQty() { return leftoverQty; }
    public void setLeftoverQty(double leftoverQty) { this.leftoverQty = leftoverQty; }
    public Map<String, Object> getRowData() { return rowData; }
    public void setRowData(Map<String, Object> rowData) { this.rowData = rowData; }
}
