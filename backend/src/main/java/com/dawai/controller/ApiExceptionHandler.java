package com.dawai.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ControllerAdvice;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.multipart.MultipartException;

import java.util.Map;

@ControllerAdvice
public class ApiExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(ApiExceptionHandler.class);

    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ResponseEntity<Map<String, Object>> handleMaxUploadSize(MaxUploadSizeExceededException ex) {
        log.warn("Upload rejected because payload exceeded configured limits");
        return ResponseEntity.status(HttpStatus.PAYLOAD_TOO_LARGE)
                .body(Map.of("detail", "Upload is too large. Please reduce file sizes and try again."));
    }

    @ExceptionHandler(MultipartException.class)
    public ResponseEntity<Map<String, Object>> handleMultipart(MultipartException ex) {
        if (isCausedByMaxUploadSize(ex)) {
            log.warn("Upload rejected because payload exceeded configured limits");
            return ResponseEntity.status(HttpStatus.PAYLOAD_TOO_LARGE)
                    .body(Map.of("detail", "Upload is too large. Please reduce file sizes and try again."));
        }
        log.warn("Multipart upload error: {}", ex.getMessage());
        return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(Map.of("detail", "Invalid upload request. Please verify files and retry."));
    }

    private static boolean isCausedByMaxUploadSize(Throwable ex) {
        Throwable t = ex;
        while (t != null) {
            if (t instanceof MaxUploadSizeExceededException) return true;
            t = t.getCause();
        }
        return false;
    }
}
