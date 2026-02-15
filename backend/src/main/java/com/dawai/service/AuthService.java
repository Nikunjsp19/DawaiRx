package com.dawai.service;

import com.dawai.document.RegistrationRequestDocument;
import com.dawai.document.UserDocument;
import com.dawai.dto.RequestAccessRequest;
import com.dawai.repository.AdminRepository;
import com.dawai.repository.RegistrationRequestRepository;
import com.dawai.repository.UserRepository;
import com.dawai.security.JwtService;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Page;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final RegistrationRequestRepository registrationRequestRepository;
    private final AdminRepository adminRepository;
    private final JwtService jwtService;
    private final PasswordEncoder passwordEncoder;

    public AuthService(UserRepository userRepository,
                       RegistrationRequestRepository registrationRequestRepository,
                       AdminRepository adminRepository,
                       JwtService jwtService,
                       PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.registrationRequestRepository = registrationRequestRepository;
        this.adminRepository = adminRepository;
        this.jwtService = jwtService;
        this.passwordEncoder = passwordEncoder;
    }

    public Map<String, Object> login(String userId, String password) {
        UserDocument user = userRepository.findByUserId(userId)
                .orElseThrow(() -> new RuntimeException("Invalid user ID or password"));
        if (user.getDisabled()) {
            throw new RuntimeException("This account has been disabled. Contact an administrator.");
        }
        if (user.getPasswordHash() == null || !passwordEncoder.matches(password, user.getPasswordHash())) {
            throw new RuntimeException("Invalid user ID or password");
        }
        String token = jwtService.generateToken(user.getUserId());
        return Map.of(
                "access_token", token,
                "token_type", "bearer",
                "user_id", user.getUserId()
        );
    }

    public void register(String userId, String email, String password) {
        if (userRepository.existsByUserId(userId)) {
            throw new RuntimeException("User ID already exists");
        }
        if (email != null && !email.isBlank()) {
            registrationRequestRepository.findByEmailIgnoreCase(email)
                    .filter(req -> "approved".equals(req.getStatus()))
                    .orElseThrow(() -> new RuntimeException("No approved request found for this email. Please request access first and wait for approval."));
        }
        UserDocument user = new UserDocument();
        user.setUserId(userId);
        user.setEmail(email != null ? email.trim() : null);
        user.setPasswordHash(passwordEncoder.encode(password));
        userRepository.save(user);
    }

    public Map<String, Object> requestAccess(RequestAccessRequest req) {
        RegistrationRequestDocument doc = new RegistrationRequestDocument();
        doc.setEmail(req.email().trim().toLowerCase());
        doc.setCompany(req.company().trim());
        doc.setStatus("pending");
        doc.setRequestedAt(Instant.now());
        registrationRequestRepository.save(doc);
        return Map.of(
                "message", "Registration request submitted successfully. Admin will review your request.",
                "status", "pending",
                "email", doc.getEmail()
        );
    }

    public Map<String, String> checkStatus(String email) {
        if (email == null || email.isBlank()) {
            return Map.of("status", "not_found", "message", "Enter your email to check status.");
        }
        return registrationRequestRepository.findByEmailIgnoreCase(email.trim())
                .map(req -> Map.<String, String>of(
                        "status", req.getStatus(),
                        "message", switch (req.getStatus()) {
                            case "approved" -> "Your request has been approved. You can now complete registration.";
                            case "rejected" -> "Your request was rejected. Please contact admin.";
                            default -> "Your request is pending admin approval.";
                        }
                ))
                .orElse(Map.of("status", "not_found", "message", "No registration request found for this email."));
    }

    public boolean isAdmin(String userId) {
        return userId != null && adminRepository.existsByUserId(userId);
    }

    /** Admin-only: list all users (user_id, email, disabled; no password). Excludes admin users. */
    public List<Map<String, Object>> listUsers() {
        return userRepository.findAll().stream()
                .filter(u -> u.getUserId() != null && !adminRepository.existsByUserId(u.getUserId()))
                .map(u -> {
                    Map<String, Object> m = new LinkedHashMap<>();
                    m.put("user_id", u.getUserId());
                    m.put("email", u.getEmail() != null ? u.getEmail() : "");
                    m.put("disabled", u.getDisabled());
                    return m;
                })
                .toList();
    }

    /** Admin-only: set user disabled state. Cannot disable self. */
    public void setUserDisabled(String targetUserId, boolean disabled, String adminUserId) {
        if (targetUserId == null || targetUserId.isBlank()) {
            throw new RuntimeException("User ID required");
        }
        if (targetUserId.equals(adminUserId)) {
            throw new RuntimeException("You cannot disable your own account");
        }
        UserDocument user = userRepository.findByUserId(targetUserId)
                .orElseThrow(() -> new RuntimeException("User not found"));
        user.setDisabled(disabled);
        userRepository.save(user);
    }

    @SuppressWarnings("unchecked")
    public java.util.List<Map<String, Object>> listRegistrationRequests() {
        return (java.util.List<Map<String, Object>>) listRegistrationRequests("all", 0, Integer.MAX_VALUE).get("requests");
    }

    /** Admin-only: list registration requests with pagination. Returns map with "requests" and "total". */
    public Map<String, Object> listRegistrationRequests(String statusFilter, int page, int size) {
        int safeSize = Math.max(1, Math.min(100, size));
        int pageIndex = Math.max(0, page);
        Pageable pageable = PageRequest.of(pageIndex, safeSize);
        Page<RegistrationRequestDocument> pageResult;
        long total;
        if (statusFilter != null && !statusFilter.isBlank() && !"all".equalsIgnoreCase(statusFilter)) {
            pageResult = registrationRequestRepository.findByStatusOrderByRequestedAtDesc(statusFilter, pageable);
            total = registrationRequestRepository.countByStatus(statusFilter);
        } else {
            pageResult = registrationRequestRepository.findAllByOrderByRequestedAtDesc(pageable);
            total = registrationRequestRepository.count();
        }
        List<Map<String, Object>> requests = pageResult.getContent().stream()
                .map(req -> Map.<String, Object>of(
                        "id", req.getId() != null ? req.getId() : "",
                        "user_id", req.getUserId() != null ? req.getUserId() : "",
                        "email", req.getEmail() != null ? req.getEmail() : "",
                        "company", req.getCompany() != null ? req.getCompany() : "",
                        "status", req.getStatus() != null ? req.getStatus() : "pending",
                        "requested_at", req.getRequestedAt() != null ? req.getRequestedAt().toString() : ""
                ))
                .toList();
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("requests", requests);
        body.put("total", total);
        return body;
    }

    public void approveRequest(String id, String adminUserId) {
        RegistrationRequestDocument req = registrationRequestRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Request not found"));
        req.setStatus("approved");
        req.setReviewedAt(Instant.now());
        req.setReviewedBy(adminUserId);
        registrationRequestRepository.save(req);
    }

    public void rejectRequest(String id, String adminUserId) {
        RegistrationRequestDocument req = registrationRequestRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Request not found"));
        req.setStatus("rejected");
        req.setReviewedAt(Instant.now());
        req.setReviewedBy(adminUserId);
        registrationRequestRepository.save(req);
    }
}
