package com.dawai.controller;

import com.dawai.dto.LoginRequest;
import com.dawai.dto.RegisterRequest;
import com.dawai.dto.RequestAccessRequest;
import com.dawai.security.UserContext;
import com.dawai.service.AuthService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/login")
    public ResponseEntity<Map<String, Object>> login(@Valid @RequestBody LoginRequest req) {
        Map<String, Object> body = authService.login(req.user_id(), req.password());
        return ResponseEntity.ok(body);
    }

    @PostMapping("/register")
    public ResponseEntity<Map<String, String>> register(@Valid @RequestBody RegisterRequest req) {
        authService.register(req.user_id(), req.email(), req.password());
        return ResponseEntity.ok(Map.of("message", "Registration successful. You can now log in."));
    }

    @PostMapping("/request-access")
    public ResponseEntity<Map<String, Object>> requestAccess(@Valid @RequestBody RequestAccessRequest req) {
        return ResponseEntity.ok(authService.requestAccess(req));
    }

    @GetMapping("/check-status")
    public ResponseEntity<Map<String, String>> checkStatus(@RequestParam String email) {
        return ResponseEntity.ok(authService.checkStatus(email));
    }

    @GetMapping("/me")
    public ResponseEntity<Map<String, Object>> me() {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) {
            return ResponseEntity.status(401).build();
        }
        boolean isAdmin = authService.isAdmin(userId);
        return ResponseEntity.ok(Map.of("user_id", userId, "is_admin", isAdmin));
    }
}
