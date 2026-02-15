package com.dawai.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;

public record LoginRequest(
        @JsonProperty("user_id") @NotBlank String user_id,
        @NotBlank String password
) {}
