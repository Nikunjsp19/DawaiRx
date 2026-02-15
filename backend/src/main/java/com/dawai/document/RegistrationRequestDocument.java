package com.dawai.document;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.time.Instant;

@Document(collection = "registration_requests")
public class RegistrationRequestDocument {

    @Id
    private String id;
    @Indexed
    @Field("user_id")
    private String userId;
    private String email;
    private String reason;
    private String company;
    private String status; // pending, approved, rejected
    @Field("requested_at")
    private Instant requestedAt;
    @Field("reviewed_at")
    private Instant reviewedAt;
    @Field("reviewed_by")
    private String reviewedBy;
    @Field("admin_notes")
    private String adminNotes;

    public RegistrationRequestDocument() {}

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getReason() { return reason; }
    public void setReason(String reason) { this.reason = reason; }
    public String getCompany() { return company; }
    public void setCompany(String company) { this.company = company; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public Instant getRequestedAt() { return requestedAt; }
    public void setRequestedAt(Instant requestedAt) { this.requestedAt = requestedAt; }
    public Instant getReviewedAt() { return reviewedAt; }
    public void setReviewedAt(Instant reviewedAt) { this.reviewedAt = reviewedAt; }
    public String getReviewedBy() { return reviewedBy; }
    public void setReviewedBy(String reviewedBy) { this.reviewedBy = reviewedBy; }
    public String getAdminNotes() { return adminNotes; }
    public void setAdminNotes(String adminNotes) { this.adminNotes = adminNotes; }
}
