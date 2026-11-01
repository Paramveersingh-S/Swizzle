# 🌐 Swizzle Permanent Production Domain Guide: `api.withswizzle.com`

This guide explains how to attach your Google Colab Pro GPU worker (or on-premise NVIDIA H100/A100 server) directly to **`api.withswizzle.com`** using **Cloudflare Zero Trust Named Tunnels**.

With a Named Tunnel, you **never** need to copy/paste ephemeral `.trycloudflare.com` URLs again. The worker permanently routes to your domain with zero port-forwarding and enterprise TLS termination.

---

## 🛠️ Step-by-Step Setup (One-time, 3 minutes)

### 1. Create Tunnel in Cloudflare Zero Trust
1. Go to the [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/).
2. In the left navigation, open **Networks** > **Tunnels**.
3. Click **Add a tunnel** and select **Cloudflare (recommended)**.
4. Name the tunnel: `swizzle-inference-tunnel` and click **Save tunnel**.

### 2. Copy the Tunnel Token
Under the install instructions (e.g., Docker or Linux), locate the token flag:
```bash
cloudflared service install eyJh...[LONG_BASE64_TOKEN]...
```
Copy just the token string (`eyJh...`).

### 3. Configure the Public Hostname
On the **Public Hostnames** tab of the tunnel:
* **Subdomain**: `api`
* **Domain**: `withswizzle.com`
* **Path**: *(leave empty)*
* **Type**: `HTTP`
* **URL**: `localhost:8000` (or `localhost:8080` if routing through the Go Token Optimizer Gateway)

Click **Save hostname**. Cloudflare will automatically create the DNS CNAME record for `api.withswizzle.com`.

---

## 🚀 Running on Colab Pro Worker

In [`colab_worker.ipynb`](../colab_worker.ipynb), Cell 4 has an input field:
```python
# Paste your token here to bind permanently to api.withswizzle.com
CLOUDFLARE_TUNNEL_TOKEN = "eyJh..."
```

When you execute Cell 4 with the token:
1. `cloudflared` authenticates with Cloudflare Zero Trust.
2. `api.withswizzle.com` is immediately alive with HTTPS.
3. The watchdog keeps the tunnel connected and auto-reconnects if disconnected.

*(If `CLOUDFLARE_TUNNEL_TOKEN` is left blank, it automatically defaults to an instant public `*.trycloudflare.com` URL.)*

---

## 💻 Running on Linux / Docker (Self-Hosted / RunPod)

To run as a systemd service or daemon on an on-premise node:

```bash
# Run directly with token
cloudflared tunnel --no-autoupdate run --token <TUNNEL_TOKEN>
```

Or using Docker:
```bash
docker run -d --network host --restart always cloudflare/cloudflared:latest tunnel --no-autoupdate run --token <TUNNEL_TOKEN>
```

---

## 🧪 Verification

Verify your live endpoint with a test query:

```bash
curl -i https://api.withswizzle.com/v1/models
```

Expected response:
```json
{
  "object": "list",
  "data": [
    {
      "id": "Qwen/Qwen2.5-Coder-7B-Instruct",
      "object": "model",
      "owned_by": "swizzle"
    }
  ]
}
```
