package com.dawai.dto;

public record TokenResponse(
        String access_token,
        String token_type,
        String user_id
) {
    public TokenResponse(String accessToken, String userId) {
        this(accessToken, "bearer", userId);
    }
}
