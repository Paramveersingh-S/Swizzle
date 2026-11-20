# Swizzle Enterprise 14-Day Shadow Pilot Guide

Swizzle deploys cleanly inside your own VPC or Kubernetes cluster with **zero data leaving your network** (`Zero-Data-Retention` ephemeral secret scrubbing + local/self-hosted inference).

---

## 1. What Problem the Shadow Pilot Proves in 14 Days

1. **Prefix Cache & Cost Collapse (`Swizzle-Tree` AST-Diff KV Paging):**
   - Multi-turn coding and tool-use agents resend 80–95% shared context while invalidating linear prefix caches on small edits.
   - `Swizzle-Tree` canonicalizes unchanged AST blocks first (`89.6%` cache reuse vs `48.0%` linear in our agent traces) while routing to OpenAI/Anthropic/vLLM or `swizzle-rt`.
2. **Code-Edit Fast-Apply (`RAD-1` + OpenAI `prediction`):**
   - Standard `/v1/chat/completions` calls with `"prediction": {"type": "content", "content": "<file>"}` seed `swizzle-rt`'s suffix-automaton drafter cleanly (`5.04x` speedup vs `llama.cpp` measured on NVIDIA L4 `Qwen2.5-7B-Instruct-Q4_K_M`).
3. **Ephemeral Secret Scrubbing (`gateway/dlp.go`) & Cryptographic Audit Trails:**
   - Detects and temporarily masks AWS (`AKIA...`), GitHub (`ghp_...`, `github_pat_...`), Slack (`xox...`), and PEM private keys in RAM before any upstream LLM call (`SecretVault`).
   - Propagates W3C `traceparent` and seals every request into an HMAC-SHA256 hash chain (`X-Swizzle-Audit-Token`), queryable live during a pilot:
     - `GET /v1/enterprise/roi` — Token/cost savings (`effective_cost_savings_pct`), `secrets_redacted_zdr`, and chain integrity (`audit_chain_verified`).
     - `GET /v1/enterprise/audit?limit=50` — Zero-Data-Retention signed receipts + `chain_valid` check for security & compliance export.

---

## 2. Quickstart: Local VPC / Docker Compose Pilot (5 Minutes)

```bash
# Set strong cluster salts before starting
export SWIZZLE_CLUSTER_SALT="$(openssl rand -hex 32)"
export SWIZZLE_KEY_PEPPER="$(openssl rand -hex 32)"
export UPSTREAM_URL="http://host.docker.internal:8080/v1"  # or your vLLM/swizzle-rt endpoint

docker compose -f deploy/docker-compose.enterprise.yml up -d
```

Point any OpenAI or Anthropic client (`Continue`, `Cline`, `LiteLLM`, `Claude Code`) at `http://localhost:8080/v1` and scrape Prometheus telemetry at `http://localhost:9090`.

---

## 3. Kubernetes Helm Chart (`deploy/helm/swizzle-enterprise`)

```bash
helm upgrade --install swizzle deploy/helm/swizzle-enterprise \
  --set gateway.clusterSalt="$(openssl rand -hex 32)" \
  --set gateway.keyPepper="$(openssl rand -hex 32)" \
  --set runtime.modelPath="/models/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf"
```

---

## 4. Physical AI & Weight-Space Self-Healing Add-On

For robotics or edge-model teams, pair `swizzle-gateway` with:
- **`swizzle-robotics` (`Swizzle-CBF` + `MCAP`/`LeRobot` Recorder):** Real-time kinematic barrier checks + cryptographic action receipts.
- **`swizzle-wsp` (`pip install swizzle-wsp[serve]`):** Gradient-free activation/quantization repair (`Q4_0` AWQ salience preservation & `.swp.json` weight-diff verification).
