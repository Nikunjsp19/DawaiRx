package com.dawai.document;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.util.Map;

@Document(collection = "run_issues")
public class RunIssueDocument {

    @Id
    private String id;
    @Field("run_id")
    private String runId;
    @Field("user_id")
    private String userId;
    @Field("rule_id")
    private String ruleId;
    private String severity;
    @Field("medicine_key")
    private String medicineKey;
    private String details;
    @Field("row_ref")
    private Map<String, Object> rowRef;
    @Field("raw_snippet")
    private Map<String, Object> rawSnippet;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getRunId() { return runId; }
    public void setRunId(String runId) { this.runId = runId; }
    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }
    public String getRuleId() { return ruleId; }
    public void setRuleId(String ruleId) { this.ruleId = ruleId; }
    public String getSeverity() { return severity; }
    public void setSeverity(String severity) { this.severity = severity; }
    public String getMedicineKey() { return medicineKey; }
    public void setMedicineKey(String medicineKey) { this.medicineKey = medicineKey; }
    public String getDetails() { return details; }
    public void setDetails(String details) { this.details = details; }
    public Map<String, Object> getRowRef() { return rowRef; }
    public void setRowRef(Map<String, Object> rowRef) { this.rowRef = rowRef; }
    public Map<String, Object> getRawSnippet() { return rawSnippet; }
    public void setRawSnippet(Map<String, Object> rawSnippet) { this.rawSnippet = rawSnippet; }
}
