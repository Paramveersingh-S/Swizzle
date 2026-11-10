import pytest
from swizzle.engine.llm_engine import LLMEngine
from swizzle.engine.sequence import SamplingParams


def test_llm_engine_end_to_end_generation():
    engine = LLMEngine(
        model_name="Qwen/Qwen2.5-Coder-7B-Instruct",
        num_blocks=128,
        block_size=8,
        enable_speculative=True,
        enable_prefix_cache=True,
    )

    # Submit 2 concurrent requests
    engine.add_request(
        request_id="req-agent-1",
        prompt_tokens=[10, 20, 30, 40, 50, 60, 70, 80],
        sampling_params=SamplingParams(max_tokens=6, temperature=0.2),
    )
    engine.add_request(
        request_id="req-agent-2",
        prompt_tokens=[10, 20, 30, 40, 99, 100, 101, 102],
        sampling_params=SamplingParams(max_tokens=4, temperature=0.2),
    )

    completed_outputs = {}
    steps = 0
    max_steps = 25

    while engine.has_unfinished_requests() and steps < max_steps:
        outputs = engine.step()
        for out in outputs:
            if out.finished:
                completed_outputs[out.request_id] = out
        steps += 1

    assert "req-agent-1" in completed_outputs
    assert "req-agent-2" in completed_outputs

    out1 = completed_outputs["req-agent-1"]
    assert out1.finished is True
    assert len(out1.output_tokens) >= 4
    assert "ttft_ms" in out1.telemetry
    assert "speculative_speedup" in out1.telemetry
    assert "cache_hit_tokens" in out1.telemetry

    engine_stats = engine.get_engine_stats()
    assert engine_stats["step_counter"] > 0
    assert engine_stats["unfinished_requests"] == 0

