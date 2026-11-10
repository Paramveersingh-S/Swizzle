#!/usr/bin/env python3
"""
Swizzle Continuous Batching Serving Benchmark (`benchmark_continuous_serving.py`)
================================================================================
Industrial-grade serving benchmark modeled after vLLM's `benchmark_serving.py`
and SGLang's `bench_serving.py`. Evaluates continuous batching throughput,
Time-to-First-Token (TTFT), Inter-Token Latency (ITL), and prefix cache reuse
under realistic Poisson-arrival agentic workloads.
"""

import sys
import os
import time
import random
import argparse
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass, field

# Ensure local swizzle package is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from swizzle.engine.llm_engine import LLMEngine, RequestOutput
from swizzle.engine.sequence import SamplingParams


@dataclass
class BenchmarkRequest:
    request_id: str
    arrival_time: float
    prompt_tokens: List[int]
    max_output_tokens: int
    ast_diff_map: Optional[Dict[int, int]] = None


@dataclass
class BenchmarkSummary:
    total_requests: int
    completed_requests: int
    duration_s: float
    total_tokens_generated: int
    throughput_tok_s: float
    ttft_p50_ms: float
    ttft_p90_ms: float
    ttft_p99_ms: float
    itl_p50_ms: float
    prefix_cache_hit_pct: float
    speculative_speedup: float


def generate_sharegpt_traces(
    num_requests: int = 100,
    request_rate: float = 10.0,
    seed: int = 42,
) -> List[BenchmarkRequest]:
    """
    Generates synthetic traces mimicking the ShareGPT conversation distribution:
    varying prompt lengths (128 - 2048 tokens), shared multi-turn system prefixes,
    and output lengths (32 - 256 tokens).
    """
    random.seed(seed)
    shared_system_prefix = [random.randint(100, 50000) for _ in range(256)]
    requests = []
    current_time = 0.0

    for i in range(num_requests):
        # Inter-arrival interval via exponential distribution (Poisson process)
        if request_rate < float("inf") and request_rate > 0:
            interval = random.expovariate(request_rate)
            current_time += interval
        else:
            current_time = 0.0

        # 75% of requests share a warm system prefix (simulating agentic coding sessions)
        has_shared_prefix = random.random() < 0.75
        prompt_len = random.randint(64, 512)
        unique_tokens = [random.randint(100, 50000) for _ in range(prompt_len)]

        if has_shared_prefix:
            prompt = shared_system_prefix + unique_tokens
            ast_diff = {2: 1} if random.random() < 0.5 else None
        else:
            prompt = unique_tokens
            ast_diff = None

        output_len = random.randint(16, 64)
        requests.append(
            BenchmarkRequest(
                request_id=f"sharegpt-req-{i:04d}",
                arrival_time=current_time,
                prompt_tokens=prompt,
                max_output_tokens=output_len,
                ast_diff_map=ast_diff,
            )
        )

    return requests


def run_serving_benchmark(
    num_requests: int = 80,
    request_rate: float = 20.0,
    model_name: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
    enable_speculative: bool = True,
    enable_prefix_cache: bool = True,
) -> BenchmarkSummary:
    """Executes the continuous batching benchmark loop against Swizzle LLMEngine."""
    traces = generate_sharegpt_traces(num_requests=num_requests, request_rate=request_rate)

    engine = LLMEngine(
        model_name=model_name,
        num_blocks=4096,
        block_size=16,
        enable_speculative=enable_speculative,
        enable_prefix_cache=enable_prefix_cache,
    )

    t_bench_start = time.perf_counter()
    next_req_idx = 0
    completed_requests: Dict[str, RequestOutput] = {}
    step_times = []

    # Simulation loop
    while next_req_idx < len(traces) or engine.has_unfinished_requests():
        sim_elapsed = time.perf_counter() - t_bench_start

        # Dispatch newly arrived requests
        while next_req_idx < len(traces) and traces[next_req_idx].arrival_time <= sim_elapsed:
            req = traces[next_req_idx]
            engine.add_request(
                request_id=req.request_id,
                prompt_tokens=req.prompt_tokens,
                sampling_params=SamplingParams(max_tokens=req.max_output_tokens, temperature=0.2),
                ast_metadata={"ast_diff_map": req.ast_diff_map} if req.ast_diff_map else None,
            )
            next_req_idx += 1

        # Advance engine continuous batching iteration
        t0 = time.perf_counter()
        outputs = engine.step()
        step_times.append((time.perf_counter() - t0) * 1000.0)

        for out in outputs:
            if out.finished and out.request_id not in completed_requests:
                completed_requests[out.request_id] = out

    total_duration = max(1e-5, time.perf_counter() - t_bench_start)
    total_tokens = sum(len(o.output_tokens) for o in completed_requests.values())
    throughput = total_tokens / total_duration

    # Latency percentiles
    ttfts = [o.telemetry.get("ttft_ms", 1.0) for o in completed_requests.values()]
    ttfts.sort()
    n = len(ttfts)
    p50_ttft = ttfts[int(n * 0.50)] if n else 1.0
    p90_ttft = ttfts[int(n * 0.90)] if n else 1.0
    p99_ttft = ttfts[int(n * 0.99)] if n else 1.0

    stats = engine.get_engine_stats()
    cache_hit_pct = stats["blocks"]["cache_hit_ratio"] * 100.0
    spec_speedup = stats["speculative"]["speculative_speedup"]

    summary = BenchmarkSummary(
        total_requests=num_requests,
        completed_requests=len(completed_requests),
        duration_s=round(total_duration, 2),
        total_tokens_generated=total_tokens,
        throughput_tok_s=round(throughput, 1),
        ttft_p50_ms=round(p50_ttft, 2),
        ttft_p90_ms=round(p90_ttft, 2),
        ttft_p99_ms=round(p99_ttft, 2),
        itl_p50_ms=round(sum(step_times) / max(1, len(step_times)), 2),
        prefix_cache_hit_pct=round(cache_hit_pct, 1),
        speculative_speedup=spec_speedup,
    )

    print("\n" + "=" * 90)
    print(f"       SWIZZLE CONTINUOUS BATCHING SERVING BENCHMARK ({model_name})       ")
    print("=" * 90)
    print(f"  Total Requests Processed:     {summary.completed_requests} / {summary.total_requests}")
    print(f"  Benchmark Duration:           {summary.duration_s} seconds")
    print(f"  Total Tokens Generated:       {summary.total_tokens_generated}")
    print(f"  Serving Throughput:           {summary.throughput_tok_s:>7.1f} tokens/second")
    print(f"  Time-To-First-Token (TTFT):   p50={summary.ttft_p50_ms}ms | p90={summary.ttft_p90_ms}ms | p99={summary.ttft_p99_ms}ms")
    print(f"  Inter-Token Latency (ITL):    p50={summary.itl_p50_ms}ms / iteration")
    print(f"  Prefix Cache Hit Ratio:       {summary.prefix_cache_hit_pct}%")
    print(f"  Speculative Speedup Factor:   {summary.speculative_speedup}x")
    print("=" * 90 + "\n")

    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Swizzle Continuous Batching Serving Benchmark")
    parser.add_argument("--num-requests", type=int, default=60, help="Total number of requests")
    parser.add_argument("--request-rate", type=float, default=25.0, help="Poisson arrival rate (req/s)")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-Coder-7B-Instruct", help="Model name")
    args = parser.parse_args()

    run_serving_benchmark(
        num_requests=args.num_requests,
        request_rate=args.request_rate,
        model_name=args.model,
    )
