# Swizzle Upstream Distribution PR Pack

Ready-to-open upstream integration PRs putting **`swizzle-rt` (`5.04x` `RAD-1` code-edit Fast-Apply)** and **`swizzle-gateway` (`Swizzle-Tree` AST prefix reuse + `SecretVault` DLP + `X-Swizzle-Audit-Token`)** in front of coding-agent developers.

---

## PR 1: `BerriAI/litellm` — Native `swizzle/` Provider + Telemetry Header Pass-Through

- **Target Path in `BerriAI/litellm`:** `litellm/llms/swizzle/chat/transformation.py` (extends OpenAI-compatible config cleanly) or custom handler tested locally in [`integrations/litellm_swizzle_provider.py`](./litellm_swizzle_provider.py).
- **PR Title:** `feat(providers): add Swizzle Runtime & Gateway OpenAI provider with Predicted Outputs telemetry`
- **Key Features Included:**
  - Passes standard OpenAI `prediction: {"type": "content", "content": ...}` straight to `swizzle-rt` / `swizzle-gateway` (`5.04x` faster `edit256` measured on NVIDIA L4 `Qwen2.5-7B-Instruct-Q4_K_M`).
  - Forwards W3C `traceparent` headers and surfaces `X-Swizzle-Audit-Token`, `X-Swizzle-Saved-USD`, `X-Swizzle-AST-Reuse-Pct`, and `X-Swizzle-Cache-Hit-Tokens`.
- **Verification Command:** `pytest tests/test_integrations_pr_kits.py`

---

## PR 2: `continuedev/continue` — Drop-in Fast-Apply & Autocomplete Provider (`localhost:8080/v1`)

- **Local Ready Config:** [`integrations/continue_config.json`](./continue_config.json)
- **PR Title:** `docs(providers): add Swizzle Runtime local Fast-Apply provider preset`
- **Why Continue Maintainers Merge It:**
  - Uses standard `provider: "openai"` with `apiBase: "http://localhost:8080/v1"` (`swizzle-rt serve` or `swizzle-gateway`) and enables `"roles": ["chat", "edit", "apply"]` so Continue's file-apply requests leverage `RAD-1` suffix-automaton prediction without new SDK deps.

---

## PR 3: `cline/cline` — Enterprise VPC + Zero-Data-Retention Coding Backend

- **PR Title:** `docs(api-providers): add Swizzle VPC Gateway preset for local Fast-Apply & ZDR secret scrubbing`
- **Setup Steps for Cline Users:**
  1. Start `swizzle-gateway` (`docker compose -f deploy/docker-compose.enterprise.yml up -d`) or `swizzle-rt serve Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf --port 8080`.
  2. In Cline Settings -> API Provider: select **OpenAI Compatible**.
  3. Set Base URL: `http://localhost:8080/v1`, API Key: `sk-swizzle-dev-bypass-key` (or issued tenant key), Model ID: `Qwen/Qwen2.5-Coder-7B-Instruct`.
  4. Inspect savings and secret scrubbing live at `http://localhost:8080/v1/enterprise/roi` and tamper-evident receipts at `http://localhost:8080/v1/enterprise/audit`.
