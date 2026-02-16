package com.dawai.document;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.util.Date;
import java.util.Map;

@Document(collection = "runs")
public class RunDocument {

    @Id
    private String id;
    @Indexed(unique = true)
    @Field("run_id")
    private String runId;
    @Indexed
    @Field("user_id")
    private String userId;
    @Field("created_at")
    private Date createdAt;
    @Field("input_metadata")
    private Map<String, Object> inputMetadata;
    private Map<String, Object> stats;
    @Field("config_summary")
    private Map<String, Object> configSummary;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getRunId() { return runId; }
    public void setRunId(String runId) { this.runId = runId; }
    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }
    public Date getCreatedAt() { return createdAt; }
    public void setCreatedAt(Date createdAt) { this.createdAt = createdAt; }
    public Map<String, Object> getInputMetadata() { return inputMetadata; }
    public void setInputMetadata(Map<String, Object> inputMetadata) { this.inputMetadata = inputMetadata; }
    public Map<String, Object> getStats() { return stats; }
    public void setStats(Map<String, Object> stats) { this.stats = stats; }
    public Map<String, Object> getConfigSummary() { return configSummary; }
    public void setConfigSummary(Map<String, Object> configSummary) { this.configSummary = configSummary; }
}
