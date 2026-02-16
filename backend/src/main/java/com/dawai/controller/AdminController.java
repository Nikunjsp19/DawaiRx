package com.dawai.controller;

import com.dawai.security.UserContext;
import com.dawai.service.AuthService;
import com.dawai.service.RunService;
import org.springframework.context.annotation.Lazy;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.ZoneOffset;
import java.time.format.DateTimeParseException;
import java.util.*;
import java.util.concurrent.TimeUnit;

@Lazy(false)
@RestController
@RequestMapping("/api/admin")
public class AdminController {

    private final AuthService authService;
    private final RunService runService;

    public AdminController(AuthService authService, RunService runService) {
        this.authService = authService;
        this.runService = runService;
    }

    @GetMapping("/is-admin")
    public ResponseEntity<Map<String, Boolean>> isAdmin() {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) {
            return ResponseEntity.status(401).build();
        }
        return ResponseEntity.ok(Map.of("is_admin", authService.isAdmin(userId)));
    }

    @GetMapping("/users")
    public ResponseEntity<Map<String, Object>> listUsers() {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) return ResponseEntity.status(401).build();
        if (!authService.isAdmin(userId)) return ResponseEntity.status(403).build();
        List<Map<String, Object>> users = authService.listUsers();
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("users", users);
        return ResponseEntity.ok(body);
    }

    @PostMapping("/users/{targetUserId}/disable")
    public ResponseEntity<Map<String, String>> disableUser(@PathVariable String targetUserId) {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) return ResponseEntity.status(401).build();
        if (!authService.isAdmin(userId)) return ResponseEntity.status(403).build();
        authService.setUserDisabled(targetUserId, true, userId);
        return ResponseEntity.ok(Map.of("message", "User disabled"));
    }

    @PostMapping("/users/{targetUserId}/enable")
    public ResponseEntity<Map<String, String>> enableUser(@PathVariable String targetUserId) {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) return ResponseEntity.status(401).build();
        if (!authService.isAdmin(userId)) return ResponseEntity.status(403).build();
        authService.setUserDisabled(targetUserId, false, userId);
        return ResponseEntity.ok(Map.of("message", "User enabled"));
    }

    @DeleteMapping("/users/{targetUserId}")
    public ResponseEntity<Map<String, String>> deleteUser(@PathVariable String targetUserId) {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) return ResponseEntity.status(401).build();
        if (!authService.isAdmin(userId)) return ResponseEntity.status(403).build();
        authService.deleteUser(targetUserId, userId);
        return ResponseEntity.ok(Map.of("message", "User deleted"));
    }

    @GetMapping(value = { "/report-stats", "/report_stats" }, produces = MediaType.APPLICATION_JSON_VALUE)
    public ResponseEntity<Map<String, Object>> reportStats(
            @RequestParam(required = false) Integer days,
            @RequestParam(required = false) String from_date,
            @RequestParam(required = false) String to_date,
            @RequestParam(required = false) String q) {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) return ResponseEntity.status(401).build();
        if (!authService.isAdmin(userId)) return ResponseEntity.status(403).build();

        Date from = null;
        Date to = null;
        int effectiveDays = 30;
        if (from_date != null && !from_date.isBlank() && to_date != null && !to_date.isBlank()) {
            try {
                from = Date.from(LocalDate.parse(from_date.trim()).atStartOfDay(ZoneOffset.UTC).toInstant());
                to = Date.from(LocalDate.parse(to_date.trim()).plusDays(1).atStartOfDay(ZoneOffset.UTC).toInstant());
            } catch (DateTimeParseException ignored) {
                // fall back to days
            }
        }
        if (from == null || to == null) {
            int d = (days != null) ? Math.max(1, Math.min(365, days)) : 30;
            effectiveDays = d;
            long sinceMillis = System.currentTimeMillis() - TimeUnit.DAYS.toMillis(d);
            from = new Date(sinceMillis);
            to = new Date();
        }
        List<Map<String, Object>> stats = runService.getReportCountsByUser(from, to, q).stream()
                .filter(row -> !authService.isAdmin((String) row.get("user_id")))
                .toList();
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("stats", stats);
        body.put("days", effectiveDays);
        if (from != null) body.put("from_date", from.toInstant().toString());
        if (to != null) body.put("to_date", to.toInstant().toString());
        return ResponseEntity.ok(body);
    }

    @GetMapping("/requests")
    public ResponseEntity<Map<String, Object>> listRequests(
            @RequestParam(required = false) String status_filter,
            @RequestParam(required = false, defaultValue = "1") int page,
            @RequestParam(required = false, defaultValue = "10") int limit) {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) return ResponseEntity.status(401).build();
        if (!authService.isAdmin(userId)) return ResponseEntity.status(403).build();
        String filter = (status_filter != null && !status_filter.isBlank()) ? status_filter : "all";
        return ResponseEntity.ok(authService.listRegistrationRequests(filter, page - 1, limit));
    }

    @PostMapping("/requests/{id}/approve")
    public ResponseEntity<Map<String, String>> approve(@PathVariable String id) {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) return ResponseEntity.status(401).build();
        if (!authService.isAdmin(userId)) return ResponseEntity.status(403).build();
        authService.approveRequest(id, userId);
        return ResponseEntity.ok(Map.of("message", "Request approved"));
    }

    @PostMapping("/requests/{id}/reject")
    public ResponseEntity<Map<String, String>> reject(@PathVariable String id) {
        String userId = UserContext.getCurrentUserId();
        if (userId == null) return ResponseEntity.status(401).build();
        if (!authService.isAdmin(userId)) return ResponseEntity.status(403).build();
        authService.rejectRequest(id, userId);
        return ResponseEntity.ok(Map.of("message", "Request rejected"));
    }
}
