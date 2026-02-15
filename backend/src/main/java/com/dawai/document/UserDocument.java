package com.dawai.document;

import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.index.Indexed;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

@Document(collection = "users")
public class UserDocument {

    @Id
    private String id;
    @Indexed(unique = true)
    @Field("user_id")
    private String userId;
    private String email;
    @Field("password_hash")
    private String passwordHash;
    @Field("disabled")
    private Boolean disabled;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getUserId() { return userId; }
    public void setUserId(String userId) { this.userId = userId; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    public String getPasswordHash() { return passwordHash; }
    public void setPasswordHash(String passwordHash) { this.passwordHash = passwordHash; }
    public Boolean getDisabled() { return Boolean.TRUE.equals(disabled); }
    public void setDisabled(Boolean disabled) { this.disabled = disabled; }
}
