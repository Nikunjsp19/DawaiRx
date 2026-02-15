package com.dawai.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public record RequestAccessRequest(
        @NotBlank @Email String email,
        @NotBlank @JsonProperty("company") String company
) {}
