import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from integrations.litellm_swizzle_provider import SwizzleOpenAIProvider


ROOT = Path(__file__).resolve().parent.parent


class _MockSwizzleHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length).decode("utf-8"))
        assert body.get("prediction", {}).get("type") == "content"
        assert self.headers.get("traceparent") == "00-abcd-01-01"

        resp = json.dumps({
            "id": "chatcmpl-test",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}}],
        }).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Swizzle-Audit-Token", "hmac-sha256:deadbeef")
        self.send_header("X-Swizzle-AST-Reuse-Pct", "89.6%")
        self.send_header("X-Swizzle-Secrets-Redacted", "1")
        self.send_header("X-Swizzle-Prediction-Seed-Tokens", "128")
        self.end_headers()
        self.wfile.write(resp)

    def log_message(self, format, *args):
        return


def test_litellm_swizzle_provider_prediction_and_audit_headers():
    server = HTTPServer(("127.0.0.1", 0), _MockSwizzleHandler)
    port = server.server_port
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        client = SwizzleOpenAIProvider(api_base=f"http://127.0.0.1:{port}/v1", api_key="sk-test")
        res = client.completion(
            model="Qwen/Qwen2.5-Coder-7B-Instruct",
            messages=[{"role": "user", "content": "Refactor foo"}],
            prediction_content="def foo():\n    return 1\n",
            traceparent="00-abcd-01-01",
        )
        assert res["choices"][0]["message"]["content"] == "ok"
        assert res["swizzle_headers"]["audit_token"] == "hmac-sha256:deadbeef"
        assert res["swizzle_headers"]["ast_reuse_pct"] == "89.6%"
        assert res["swizzle_headers"]["secrets_redacted"] == "1"
        assert res["swizzle_headers"]["prediction_seed_tokens"] == "128"
    finally:
        server.shutdown()


def test_integration_manifests_parse_cleanly():
    cont = json.loads((ROOT / "integrations" / "continue_config.json").read_text(encoding="utf-8"))
    assert cont["models"][0]["apiBase"] == "http://localhost:8080/v1"
    assert "apply" in cont["models"][0]["roles"]
