import pytest
import sys
import os

from benchmarks.benchmark_continuous_serving import (
    generate_sharegpt_traces,
    run_serving_benchmark,
)


def test_generate_sharegpt_traces():
    traces = generate_sharegpt_traces(num_requests=10, request_rate=5.0)
    assert len(traces) == 10
    assert traces[0].request_id == "sharegpt-req-0000"
    assert len(traces[0].prompt_tokens) > 0


def test_run_serving_benchmark_fast():
    summary = run_serving_benchmark(
        num_requests=15,
        request_rate=50.0,
        model_name="Qwen/Qwen2.5-Coder-7B-Instruct",
    )
    assert summary.completed_requests == 15
    assert summary.total_tokens_generated > 0
    assert summary.throughput_tok_s > 0
    assert summary.ttft_p50_ms > 0

