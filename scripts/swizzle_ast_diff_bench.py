#!/usr/bin/env python3
"""
Swizzle-Tree: AST-Diff Aware KV Virtual Paging & Non-Linear Prefix Caching Benchmark
Compares standard Linear Prefix Caching (vLLM / RadixAttention) vs. Swizzle-Tree
across a realistic multi-turn autonomous coding agent session.
"""

import sys
from dataclasses import dataclass
from typing import List, Dict, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


@dataclass
class CodeBlock:
    name: str
    kind: str
    tokens: int
    content: str
    version: int = 1

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.name}:v{self.version}"


class AgentRepoFile:
    """Simulates a multi-function source file undergoing multi-turn edits."""
    def __init__(self):
        self.blocks = [
            CodeBlock("package_and_imports", "import", 180, "package core\nimport (\n  \"context\"\n  \"net/http\"\n)"),
            CodeBlock("ConfigStruct", "type", 140, "type Config struct { Port int; Host string; MaxConns int }"),
            CodeBlock("TelemetryClient", "type", 160, "type TelemetryClient struct { Endpoint string; RateLimit int }"),
            CodeBlock("InitializeRouter", "func", 380, "func InitializeRouter(cfg Config) *http.ServeMux { ... }"),
            CodeBlock("ValidateRequestAuth", "func", 420, "func ValidateRequestAuth(r *http.Request) (string, error) { ... }"),
            CodeBlock("ProcessPayload", "func", 650, "func ProcessPayload(ctx context.Context, data []byte) ([]byte, error) { ... }"),
            CodeBlock("ExecuteDBQuery", "func", 520, "func ExecuteDBQuery(ctx context.Context, query string) (Result, error) { ... }"),
            CodeBlock("FormatResponseJSON", "func", 340, "func FormatResponseJSON(res Result) ([]byte, error) { ... }"),
            CodeBlock("EmitAuditMetrics", "func", 290, "func EmitAuditMetrics(latencyMs int, status int) { ... }"),
            CodeBlock("GracefulShutdown", "func", 240, "func GracefulShutdown(srv *http.Server) error { ... }"),
        ]

    def total_tokens(self) -> int:
        return sum(b.tokens for b in self.blocks)

    def modify_block(self, name: str, token_delta: int = 0):
        for b in self.blocks:
            if b.name == name:
                b.version += 1
                b.tokens += token_delta
                return

    def add_block(self, block: CodeBlock):
        self.blocks.append(block)


@dataclass
class TurnResult:
    turn: int
    edit_description: str
    total_tokens: int
    linear_cached_tokens: int
    linear_cache_ratio: float
    linear_ttft_ms: float
    swizzle_cached_tokens: int
    swizzle_cache_ratio: float
    swizzle_ttft_ms: float
    tokens_saved_from_prefill: int
    prefill_flops_reduction_pct: float


def run_ast_diff_simulation():
    repo = AgentRepoFile()
    
    # Roofline timing model (A100 SXM4):
    # - Prefill latency: ~0.018 ms per token
    # - Cached read latency: ~0.001 ms per token
    PREFILL_MS_PER_TOK = 0.018
    CACHED_MS_PER_TOK = 0.001

    edit_turns = [
        ("Turn 1: Initial cold load of repository file", None, 0),
        ("Turn 2: Agent edits ValidateRequestAuth (early function)", "ValidateRequestAuth", 25),
        ("Turn 3: Agent edits FormatResponseJSON (middle function)", "FormatResponseJSON", -15),
        ("Turn 4: Agent edits InitializeRouter (top-level router)", "InitializeRouter", 40),
        ("Turn 5: Agent modifies ConfigStruct (early type definition)", "ConfigStruct", 10),
        ("Turn 6: Agent edits EmitAuditMetrics (tail function)", "EmitAuditMetrics", 15),
        ("Turn 7: Agent adds new HealthCheckHandler (new block)", "ADD", 180),
        ("Turn 8: Agent edits ProcessPayload (core heavy function)", "ProcessPayload", 35),
    ]

    results: List[TurnResult] = []
    prev_blocks: List[CodeBlock] = []

    for turn_idx, (desc, target_name, delta) in enumerate(edit_turns, start=1):
        if target_name == "ADD":
            repo.add_block(CodeBlock("HealthCheckHandler", "func", delta, "func HealthCheckHandler(w http.ResponseWriter) { ... }"))
        elif target_name is not None:
            repo.modify_block(target_name, delta)

        current_blocks = [CodeBlock(b.name, b.kind, b.tokens, b.content, b.version) for b in repo.blocks]
        total_tokens = repo.total_tokens()

        if turn_idx == 1:
            # Cold load
            linear_cached = 0
            swizzle_cached = 0
        else:
            # 1. Standard Linear Prefix Caching (Radix Attention)
            # Fails as soon as the first divergence occurs!
            linear_cached = 0
            for prev_b, cur_b in zip(prev_blocks, current_blocks):
                if prev_b.key == cur_b.key:
                    linear_cached += cur_b.tokens
                else:
                    break  # Linear prefix broken! All downstream blocks invalidated!

            # 2. Swizzle-Tree AST-Diff Aware Virtual Paging
            # Evaluates each block independently and canonically packs unchanged blocks!
            prev_key_map = {b.name: b.key for b in prev_blocks}
            swizzle_cached = 0
            for cur_b in current_blocks:
                if cur_b.name in prev_key_map and prev_key_map[cur_b.name] == cur_b.key:
                    swizzle_cached += cur_b.tokens

        linear_ratio = (linear_cached / total_tokens) * 100.0
        swizzle_ratio = (swizzle_cached / total_tokens) * 100.0

        linear_prefill = total_tokens - linear_cached
        swizzle_prefill = total_tokens - swizzle_cached

        linear_ttft = (linear_prefill * PREFILL_MS_PER_TOK) + (linear_cached * CACHED_MS_PER_TOK)
        swizzle_ttft = (swizzle_prefill * PREFILL_MS_PER_TOK) + (swizzle_cached * CACHED_MS_PER_TOK)

        tokens_saved = swizzle_cached - linear_cached
        flops_reduction = (tokens_saved / max(1, linear_prefill)) * 100.0 if linear_prefill > 0 else 0.0

        results.append(TurnResult(
            turn=turn_idx,
            edit_description=desc,
            total_tokens=total_tokens,
            linear_cached_tokens=linear_cached,
            linear_cache_ratio=linear_ratio,
            linear_ttft_ms=linear_ttft,
            swizzle_cached_tokens=swizzle_cached,
            swizzle_cache_ratio=swizzle_ratio,
            swizzle_ttft_ms=swizzle_ttft,
            tokens_saved_from_prefill=tokens_saved,
            prefill_flops_reduction_pct=flops_reduction,
        ))

        prev_blocks = current_blocks

    return results


def main():
    print("=" * 95)
    print("[SWIZZLE-TREE] AST-DIFF AWARE KV VIRTUAL PAGING BENCHMARK")
    print("Multi-Turn Agent Refactoring Session on a 3,300+ Token Codebase (8 Turns)")
    print("Hardware Profile: NVIDIA A100 SXM4 (Prefill: 0.018 ms/tok | Cached Read: 0.001 ms/tok)")
    print("=" * 95)

    results = run_ast_diff_simulation()

    print(f"\n{'Turn':<6} | {'Linear Hit %':<14} | {'Linear TTFT':<12} | {'Swizzle Hit %':<15} | {'Swizzle TTFT':<13} | {'Tokens Saved'}")
    print("-" * 95)

    for r in results:
        print(f"Turn {r.turn:<2} | {r.linear_cache_ratio:>6.1f}% ({r.linear_cached_tokens:>4}t)  | {r.linear_ttft_ms:>6.1f} ms    | {r.swizzle_cache_ratio:>7.1f}% ({r.swizzle_cached_tokens:>4}t)  | {r.swizzle_ttft_ms:>6.1f} ms     | +{r.tokens_saved_from_prefill:>4} tokens")
        print(f"       Action: {r.edit_description}")

    # Aggregate summaries across warm turns (turns 2 through 8)
    warm_turns = results[1:]
    mean_linear_hit = sum(r.linear_cache_ratio for r in warm_turns) / len(warm_turns)
    mean_swizzle_hit = sum(r.swizzle_cache_ratio for r in warm_turns) / len(warm_turns)
    mean_linear_ttft = sum(r.linear_ttft_ms for r in warm_turns) / len(warm_turns)
    mean_swizzle_ttft = sum(r.swizzle_ttft_ms for r in warm_turns) / len(warm_turns)
    total_tokens_saved = sum(r.tokens_saved_from_prefill for r in warm_turns)
    speedup_ttft = mean_linear_ttft / mean_swizzle_ttft

    print("\n" + "=" * 95)
    print("[SUMMARY] MULTI-TURN WARM CACHE EFFICIENCY SUMMARY (Turns 2-8)")
    print(f"   * Standard Linear Prefix Hit Rate:  {mean_linear_hit:.1f}%")
    print(f"   * Swizzle-Tree AST Virtual Hit Rate: {mean_swizzle_hit:.1f}% (+{mean_swizzle_hit - mean_linear_hit:.1f}% absolute gain!)")
    print(f"   * Standard Linear Mean TTFT:        {mean_linear_ttft:.1f} ms")
    print(f"   * Swizzle-Tree Mean TTFT:           {mean_swizzle_ttft:.1f} ms ({speedup_ttft:.2f}x faster TTFT)")
    print(f"   * Cumulative Redundant Prefill Saved: {total_tokens_saved:,} tokens eliminated across 7 turns")
    print("=" * 95)


if __name__ == "__main__":
    main()
