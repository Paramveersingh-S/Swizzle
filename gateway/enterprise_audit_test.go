package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
)

func TestTier2EnterpriseROIAndAuditChain(t *testing.T) {
	_ = os.Setenv("SWIZZLE_DISABLE_UPSTREAM", "1")
	defer os.Unsetenv("SWIZZLE_DISABLE_UPSTREAM")

	enterpriseAudit = NewEnterpriseAuditLedger()
	ledger = NewPrefixCacheLedger()
	prefixRouter = NewRadixPrefixRouter()

	// Include a simulated AWS key so ZDR SecretVault scrubbing is captured in audit receipts
	sharedCtx := strings.Repeat("func routerDispatch(ctx context.Context) { /* shared code prefix */ }\n", 14)
	payload := map[string]any{
		"model": "Qwen/Qwen2.5-Coder-7B-Instruct",
		"messages": []map[string]string{
			{"role": "system", "content": sharedCtx},
			{"role": "user", "content": "Deploy with key AKIAIOSFODNN7EXAMPLE123"},
		},
	}
	body, _ := json.Marshal(payload)

	for i := 0; i < 2; i++ {
		req := httptest.NewRequest(http.MethodPost, "/v1/chat/completions", bytes.NewReader(body))
		req.Header.Set("traceparent", "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01")
		rec := httptest.NewRecorder()
		handleChatCompletions(rec, req)
		if rec.Code != http.StatusOK {
			t.Fatalf("chat request %d returned status %d", i+1, rec.Code)
		}
		if tok := rec.Header().Get("X-Swizzle-Audit-Token"); !strings.HasPrefix(tok, "hmac-sha256:") {
			t.Fatalf("expected X-Swizzle-Audit-Token header, got %q", tok)
		}
	}

	roiReq := httptest.NewRequest(http.MethodGet, "/v1/enterprise/roi", nil)
	roiRec := httptest.NewRecorder()
	handleEnterpriseROI(roiRec, roiReq)
	if roiRec.Code != http.StatusOK {
		t.Fatalf("roi endpoint returned %d", roiRec.Code)
	}
	var roi map[string]any
	if err := json.Unmarshal(roiRec.Body.Bytes(), &roi); err != nil {
		t.Fatalf("unmarshal roi: %v", err)
	}
	if roi["audit_chain_verified"] != true {
		t.Fatalf("expected audit_chain_verified=true, got %v", roi["audit_chain_verified"])
	}
	if uint64(roi["total_requests"].(float64)) != 2 {
		t.Fatalf("expected 2 recorded requests, got %v", roi["total_requests"])
	}
	if uint64(roi["secrets_redacted_zdr"].(float64)) < 2 {
		t.Fatalf("expected >=2 secrets scrubbed, got %v", roi["secrets_redacted_zdr"])
	}

	audReq := httptest.NewRequest(http.MethodGet, "/v1/enterprise/audit?limit=5", nil)
	audRec := httptest.NewRecorder()
	handleEnterpriseAudit(audRec, audReq)
	var aud map[string]any
	if err := json.Unmarshal(audRec.Body.Bytes(), &aud); err != nil {
		t.Fatalf("unmarshal audit: %v", err)
	}
	if aud["chain_valid"] != true {
		t.Fatalf("expected chain_valid=true, got %v", aud["chain_valid"])
	}
}

func TestTier2AuditChainTamperDetection(t *testing.T) {
	l := NewEnterpriseAuditLedger()
	l.Record("org_alpha", "enterprise", "Qwen/Qwen2.5-Coder-7B-Instruct", "", 1000, 800, 700, 120, 1, 0.02, 0.15)
	l.Record("org_alpha", "enterprise", "Qwen/Qwen2.5-Coder-7B-Instruct", "", 1000, 900, 850, 100, 0, 0.01, 0.16)
	if !l.VerifyChain() {
		t.Fatal("freshly signed audit chain should verify cleanly")
	}
	// Mutate a historical field without re-signing -> chain verification MUST fail
	l.mu.Lock()
	l.entries[0].SavedUSD = 999.0
	l.mu.Unlock()
	if l.VerifyChain() {
		t.Fatal("expected VerifyChain to detect tampered historical audit entry")
	}
}
