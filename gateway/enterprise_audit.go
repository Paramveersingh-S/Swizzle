package main

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"strconv"
	"sync"
	"time"
)

// AuditReceipt records a Zero-Data-Retention (ZDR) inference event without storing prompt/response text.
type AuditReceipt struct {
	Seq             uint64  `json:"seq"`
	TimestampUTC    string  `json:"timestamp_utc"`
	TenantID        string  `json:"tenant_id"`
	Tier            string  `json:"tier"`
	Model           string  `json:"model"`
	Traceparent     string  `json:"traceparent,omitempty"`
	TotalTokens     int     `json:"total_tokens"`
	CachedTokens    int     `json:"cached_tokens"`
	ASTReusedTokens int     `json:"ast_reused_tokens"`
	TokensSaved     int     `json:"tokens_saved"`
	SecretsRedacted int     `json:"secrets_redacted"`
	CostUSD         float64 `json:"cost_usd"`
	SavedUSD        float64 `json:"saved_usd"`
	PrevDigest      string  `json:"prev_digest"`
	EntryDigest     string  `json:"entry_digest"`
}

// EnterpriseAuditLedger maintains an HMAC-chained ZDR audit log and ROI rollup for Tier 2 pilots.
type EnterpriseAuditLedger struct {
	mu               sync.RWMutex
	secret           []byte
	maxEntries       int
	entries          []AuditReceipt
	headDigest       string
	seq              uint64
	totalRequests    uint64
	totalTokens      uint64
	cachedTokens     uint64
	astReusedTokens  uint64
	optimizerSaved   uint64
	secretsRedacted  uint64
	totalCostUSD     float64
	totalSavedUSD    float64
	startedAt        time.Time
}

func NewEnterpriseAuditLedger() *EnterpriseAuditLedger {
	key := os.Getenv("SWIZZLE_KEY_PEPPER")
	if key == "" {
		key = "swizzle-hmac-key-pepper-2026"
	}
	return &EnterpriseAuditLedger{
		secret:     []byte(key),
		maxEntries: 1000,
		entries:    make([]AuditReceipt, 0, 128),
		headDigest: "genesis",
		startedAt:  time.Now().UTC(),
	}
}

func (l *EnterpriseAuditLedger) signEntry(e AuditReceipt) string {
	mac := hmac.New(sha256.New, l.secret)
	canonical := fmt.Sprintf(
		"%d|%s|%s|%s|%s|%s|%d|%d|%d|%d|%d|%.8f|%.8f|%s",
		e.Seq, e.TimestampUTC, e.TenantID, e.Tier, e.Model, e.Traceparent,
		e.TotalTokens, e.CachedTokens, e.ASTReusedTokens, e.TokensSaved,
		e.SecretsRedacted, e.CostUSD, e.SavedUSD, e.PrevDigest,
	)
	mac.Write([]byte(canonical))
	return "hmac-sha256:" + hex.EncodeToString(mac.Sum(nil))
}

// Record appends a signed ZDR receipt to the hash chain and updates ROI aggregates.
func (l *EnterpriseAuditLedger) Record(
	tenantID, tier, model, traceparent string,
	totalTokens, cachedTokens, astReusedTokens, tokensSaved, secretsRedacted int,
	costUSD, savedUSD float64,
) AuditReceipt {
	l.mu.Lock()
	defer l.mu.Unlock()

	l.seq++
	entry := AuditReceipt{
		Seq:             l.seq,
		TimestampUTC:    time.Now().UTC().Format(time.RFC3339Nano),
		TenantID:        tenantID,
		Tier:            tier,
		Model:           model,
		Traceparent:     traceparent,
		TotalTokens:     totalTokens,
		CachedTokens:    cachedTokens,
		ASTReusedTokens: astReusedTokens,
		TokensSaved:     tokensSaved,
		SecretsRedacted: secretsRedacted,
		CostUSD:         costUSD,
		SavedUSD:        savedUSD,
		PrevDigest:      l.headDigest,
	}
	entry.EntryDigest = l.signEntry(entry)
	l.headDigest = entry.EntryDigest

	if len(l.entries) >= l.maxEntries {
		copy(l.entries, l.entries[1:])
		l.entries = l.entries[:len(l.entries)-1]
	}
	l.entries = append(l.entries, entry)

	l.totalRequests++
	if totalTokens > 0 {
		l.totalTokens += uint64(totalTokens)
	}
	if cachedTokens > 0 {
		l.cachedTokens += uint64(cachedTokens)
	}
	if astReusedTokens > 0 {
		l.astReusedTokens += uint64(astReusedTokens)
	}
	if tokensSaved > 0 {
		l.optimizerSaved += uint64(tokensSaved)
	}
	if secretsRedacted > 0 {
		l.secretsRedacted += uint64(secretsRedacted)
	}
	l.totalCostUSD += costUSD
	l.totalSavedUSD += savedUSD
	return entry
}

// VerifyChain validates the cryptographic HMAC continuity of all retained receipts.
func (l *EnterpriseAuditLedger) VerifyChain() bool {
	l.mu.RLock()
	defer l.mu.RUnlock()

	if len(l.entries) == 0 {
		return l.headDigest == "genesis"
	}
	for i, e := range l.entries {
		expected := l.signEntry(e)
		if !hmac.Equal([]byte(e.EntryDigest), []byte(expected)) {
			return false
		}
		if i > 0 && e.PrevDigest != l.entries[i-1].EntryDigest {
			return false
		}
	}
	return l.entries[len(l.entries)-1].EntryDigest == l.headDigest
}

// SnapshotROI returns aggregate Tier 2 pilot savings and security telemetry.
func (l *EnterpriseAuditLedger) SnapshotROI(filterTenant string) map[string]any {
	chainOK := l.VerifyChain()
	l.mu.RLock()
	defer l.mu.RUnlock()

	var reqs, totTok, cachedTok, astTok, savedTok, secrets uint64
	var cost, saved float64

	if filterTenant == "" {
		reqs = l.totalRequests
		totTok = l.totalTokens
		cachedTok = l.cachedTokens
		astTok = l.astReusedTokens
		savedTok = l.optimizerSaved
		secrets = l.secretsRedacted
		cost = l.totalCostUSD
		saved = l.totalSavedUSD
	} else {
		for _, e := range l.entries {
			if e.TenantID != filterTenant {
				continue
			}
			reqs++
			totTok += uint64(e.TotalTokens)
			cachedTok += uint64(e.CachedTokens)
			astTok += uint64(e.ASTReusedTokens)
			savedTok += uint64(e.TokensSaved)
			secrets += uint64(e.SecretsRedacted)
			cost += e.CostUSD
			saved += e.SavedUSD
		}
	}

	grossBaseline := cost + saved
	savingsPct := 0.0
	if grossBaseline > 0 {
		savingsPct = (saved / grossBaseline) * 100.0
	}
	return map[string]any{
		"object":                     "swizzle.enterprise.roi",
		"zero_data_retention":        true,
		"tenant_filter":              filterTenant,
		"window_started_utc":         l.startedAt.Format(time.RFC3339),
		"total_requests":             reqs,
		"total_input_tokens":         totTok,
		"prefix_cached_tokens":       cachedTok,
		"ast_reused_tokens":          astTok,
		"optimizer_tokens_saved":     savedTok,
		"secrets_redacted_zdr":       secrets,
		"total_billed_usd":           cost,
		"total_saved_usd":            saved,
		"effective_cost_savings_pct": savingsPct,
		"audit_chain_verified":       chainOK,
		"audit_head_digest":          l.headDigest,
	}
}

var enterpriseAudit = NewEnterpriseAuditLedger()

func handleEnterpriseROI(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	tenant := r.URL.Query().Get("tenant_id")
	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(enterpriseAudit.SnapshotROI(tenant))
}

func handleEnterpriseAudit(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	limit := 50
	if raw := r.URL.Query().Get("limit"); raw != "" {
		if parsed, err := strconv.Atoi(raw); err == nil && parsed > 0 && parsed <= 500 {
			limit = parsed
		}
	}
	chainValid := enterpriseAudit.VerifyChain()

	enterpriseAudit.mu.RLock()
	n := len(enterpriseAudit.entries)
	start := 0
	if n > limit {
		start = n - limit
	}
	slice := make([]AuditReceipt, n-start)
	copy(slice, enterpriseAudit.entries[start:])
	head := enterpriseAudit.headDigest
	total := enterpriseAudit.totalRequests
	enterpriseAudit.mu.RUnlock()

	w.Header().Set("Content-Type", "application/json")
	_ = json.NewEncoder(w).Encode(map[string]any{
		"object":         "swizzle.enterprise.audit_log",
		"chain_valid":    chainValid,
		"head_digest":    head,
		"total_recorded": total,
		"entries":        slice,
	})
}
