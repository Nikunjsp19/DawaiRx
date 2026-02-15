package com.dawai.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RegisterRequest(
        @NotBlank @Size(min = 3, max = 50) String user_id,
        String email,
        @NotBlank @Size(min = 6) String password
) {}
