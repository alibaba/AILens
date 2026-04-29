package com.alibaba.gateway.api;

import com.alibaba.gateway.common.ApiResponse;
import com.alibaba.gateway.model.TraceQueryRequest;
import com.alibaba.gateway.model.TraceStatQueryRequest;
import com.alibaba.gateway.service.TraceQueryService;
import com.alibaba.gateway.traceql.TraceQLParseException;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/trace")
@RequiredArgsConstructor
@Slf4j
public class TraceQueryController {

    private final TraceQueryService traceQueryService;

    @PostMapping("/query")
    public ResponseEntity<ApiResponse<List<Map<String, Object>>>> query(
            @Valid @RequestBody TraceQueryRequest request) {
        return ResponseEntity.ok(ApiResponse.ok(traceQueryService.query(request)));
    }

    @PostMapping("/stat/query")
    public ResponseEntity<ApiResponse<Map<String, Object>>> statQuery(
            @Valid @RequestBody TraceStatQueryRequest request) {
        return ResponseEntity.ok(ApiResponse.ok(traceQueryService.statQuery(request)));
    }

    @ExceptionHandler(TraceQLParseException.class)
    public ResponseEntity<ApiResponse<Void>> handleParseException(TraceQLParseException ex) {
        log.warn("TraceQL parse error: {}", ex.getMessage());
        return ResponseEntity.badRequest()
                .body(ApiResponse.error(400, "Invalid TraceQL: " + ex.getMessage()));
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ApiResponse<Void>> handleIllegalArg(IllegalArgumentException ex) {
        return ResponseEntity.badRequest().body(ApiResponse.error(400, ex.getMessage()));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidation(MethodArgumentNotValidException ex) {
        String msg = ex.getBindingResult().getFieldErrors().stream()
                .map(e -> e.getField() + " " + e.getDefaultMessage())
                .collect(Collectors.joining(", "));
        return ResponseEntity.badRequest().body(ApiResponse.error(400, msg));
    }
}
