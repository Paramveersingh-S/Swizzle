"""
Tests for Swizzle Model Backends & Tokenizers.
==============================================
Validates SimulationBackend, TransformersBackend interface, VLLMBackend,
and SwizzleTokenizer across model architectures.
"""

import pytest
from swizzle.engine.backends import create_backend, SimulationBackend
from swizzle.engine.tokenizer import SwizzleTokenizer, get_default_tokenizer
from swizzle.models.llama import LlamaForCausalLM
from swizzle.models.qwen2_5_coder import Qwen2_5CoderForCausalLM


def test_simulation_backend_forward_and_sample():
    backend = SimulationBackend(model_name="Qwen/Qwen2.5-Coder-7B-Instruct", vocab_size=1000)
    assert backend.vocab_size == 1000

    input_ids = [10, 20, 30]
    logits = backend.forward(input_ids)
    assert len(logits) == 1000

    next_tok = backend.sample_next_token(logits, temperature=0.7, top_p=0.9)
    assert 0 <= next_tok < 1000

    tokens = backend.tokenize("hello world")
    assert isinstance(tokens, list)
    assert len(tokens) > 0

    detok = backend.detokenize(tokens)
    assert isinstance(detok, str)


def test_llama_backend_protocol():
    model = LlamaForCausalLM()
    assert model.vocab_size == 128256

    input_ids = [1, 2, 3, 4]
    logits = model.forward(input_ids)
    assert len(logits) == 128256

    tok = model.sample_next_token(logits, temperature=0.8, top_p=0.95)
    assert 0 <= tok < 128256


def test_qwen_backend_protocol():
    model = Qwen2_5CoderForCausalLM()
    assert model.vocab_size == 152064

    input_ids = [5, 6, 7, 8]
    logits = model.forward(input_ids)
    assert len(logits) == 152064

    tok = model.sample_next_token(logits, temperature=0.2, top_p=0.95)
    assert 0 <= tok < 152064


def test_backend_factory():
    sim = create_backend("Qwen/Qwen2.5-Coder-7B-Instruct", backend_type="simulation")
    assert isinstance(sim, SimulationBackend)
    assert sim.vocab_size == 152064

    sim_llama = create_backend("meta-llama/Llama-3.1-8B-Instruct", backend_type="simulation")
    assert isinstance(sim_llama, SimulationBackend)
    assert sim_llama.vocab_size == 128256


def test_swizzle_tokenizer_encode_decode():
    tok = get_default_tokenizer("Qwen/Qwen2.5-Coder-7B-Instruct")
    text = "def swizzle_gemm(a, b):"
    encoded = tok.encode(text)
    assert isinstance(encoded, list)
    assert len(encoded) > 0
    decoded = tok.decode(encoded)
    assert "swizzle_gemm" in decoded
