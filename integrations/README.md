# 🔌 Swizzle Upstream Distribution Integrations

Swizzle serves an OpenAI-compatible API featuring **sub-40ms cached TTFT**, zero shared-memory bank conflicts, and **automatic lossless prompt token optimization**.

You can drop Swizzle directly into any autonomous coding agent framework, proxy, or IDE with zero code changes.

---

## ⚡ Quick Endpoints & Keys

| Endpoint | Target | Models |
|---|---|---|
| **Production Vercel Proxy** | `https://swizzle-ten.vercel.app/v1` | `Qwen/Qwen2.5-Coder-7B-Instruct` |
| **Direct Permanent Named Tunnel** | `https://api.withswizzle.com/v1` | `Qwen/Qwen2.5-Coder-7B-Instruct`, `swizzle/qwen3.6-35b-a3b-fp8` |
| **Local Gateway (Token Optimizer)** | `http://localhost:8080/v1` | Dynamic Upstream Router |

*Developer Free Key*: `sk-swizzle-dev-bypass-key` (includes $5.00 starter credit)

---

## 🚀 Integration Guides

### 1. LiteLLM Proxy
Use Swizzle with LiteLLM to load-balance, fall back, or track token cache savings:

```bash
# 1. Start LiteLLM proxy pointing to Swizzle config
litellm --config integrations/litellm_config.yaml --port 4000
```

Verify in Python using [`integrations/litellm_proxy.py`](./litellm_proxy.py):
```bash
python integrations/litellm_proxy.py
```

### 2. OpenWebUI
Import model configurations directly into [OpenWebUI](https://openwebui.com/):
1. In OpenWebUI **Admin Settings** > **Connections** > **OpenAI API**:
   - URL: `https://swizzle-ten.vercel.app/v1` (or `https://api.withswizzle.com/v1`)
   - Key: `sk-swizzle-dev-bypass-key`
2. Models appear instantly as `Qwen/Qwen2.5-Coder-7B-Instruct` with prefix caching enabled.
3. Or import [`integrations/openwebui_config.json`](./openwebui_config.json).

### 3. Continue.dev (VS Code & Cursor Extension)
Add Swizzle for ultra-fast inline code completions and autonomous agent edits.

Add to `~/.continue/config.json` (or see [`integrations/continue_config.json`](./continue_config.json)):
```json
{
  "models": [
    {
      "title": "Swizzle Coder 7B",
      "provider": "openai",
      "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
      "apiBase": "https://swizzle-ten.vercel.app/v1",
      "apiKey": "sk-swizzle-dev-bypass-key"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Swizzle Tab Autocomplete",
    "provider": "openai",
    "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
    "apiBase": "https://swizzle-ten.vercel.app/v1",
    "apiKey": "sk-swizzle-dev-bypass-key"
  }
}
```

### 4. Claude Code CLI
Run Anthropic's Claude Code CLI routed through Swizzle:

```bash
export ANTHROPIC_BASE_URL="https://swizzle-ten.vercel.app/v1"
export ANTHROPIC_API_KEY="sk-swizzle-dev-bypass-key"
claude --model Qwen/Qwen2.5-Coder-7B-Instruct
```

### 5. Aider (Autonomous Terminal Pair Programmer)
Run Aider with prompt caching enabled:

```bash
export OPENAI_API_BASE="https://swizzle-ten.vercel.app/v1"
export OPENAI_API_KEY="sk-swizzle-dev-bypass-key"
aider --model openai/Qwen/Qwen2.5-Coder-7B-Instruct --cache-prompts
```

### 6. Cursor IDE
1. Open Cursor **Settings** > **Models**.
2. Enable **OpenAI API Key** and enter `sk-swizzle-dev-bypass-key`.
3. Under **Override OpenAI Base URL**, enter:
   ```
   https://swizzle-ten.vercel.app/v1
   ```
4. Add model name: `Qwen/Qwen2.5-Coder-7B-Instruct`.

---

## 📊 Optimizer Headers
When calling Swizzle through the Gateway, responses include real-time compression diagnostics:
* `X-Swizzle-Tokens-Saved`: Prompt tokens stripped via AST license deduplication and whitespace normalization.
* `X-Swizzle-Compression-Ratio`: Token savings factor (e.g. `1.43x` = 43% token reduction).
