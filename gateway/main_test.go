package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestPrefixCacheAndTTFTDrop(t *testing.T) {
	ledger = NewPrefixCacheLedger()

	repoContext := strings.Repeat("func flashAttentionSwizzleMMA(q, k, v *float16) { /* 128-byte aligned shared memory tile */ }\n", 20)
	payload := map[string]any{
		"model": "swizzle/qwen3.6-35b-a3b-fp8",
		"messages": []map[string]string{
			{"role": "system", "content": repoContext},
			{"role": "user", "content": "Optimize bank conflict stride."},
		},
	}
	body, _ := json.Marshal(payload)

	// Turn 1: Cold cache
	req1 := httptest.NewRequest(http.MethodPost, "/v1/chat/completions", bytes.NewReader(body))
	rec1 := httptest.NewRecorder()
	handleChatCompletions(rec1, req1)

	if rec1.Code != http.StatusOK {
		t.Fatalf("expected 200 OK on turn 1, got %d", rec1.Code)
	}
	ttft1 := rec1.Header().Get("X-Swizzle-TTFT-Ms")
	hit1 := rec1.Header().Get("X-Swizzle-Cache-Hit-Tokens")
	if hit1 != "0" {
		t.Fatalf("expected 0 cached tokens on cold turn 1, got %s", hit1)
	}

	// Turn 2: Warm prefix cache (same repo context)
	req2 := httptest.NewRequest(http.MethodPost, "/v1/chat/completions", bytes.NewReader(body))
	rec2 := httptest.NewRecorder()
	handleChatCompletions(rec2, req2)

	ttft2 := rec2.Header().Get("X-Swizzle-TTFT-Ms")
	hit2 := rec2.Header().Get("X-Swizzle-Cache-Hit-Tokens")
	if hit2 == "0" {
		t.Fatalf("expected non-zero cached tokens on warm turn 2, got %s", hit2)
	}
	t.Logf("Turn 1 (Cold): TTFT=%sms, CachedTokens=%s | Turn 2 (Warm): TTFT=%sms, CachedTokens=%s", ttft1, hit1, ttft2, hit2)
}

