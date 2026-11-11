"""
Tests for Swizzle Kernels & vLLM Plugin Registration.
=====================================================
Validates XOR swizzle index math, decode attention forward execution,
and vllm_plugin registration hook.
"""

import sys
import os
import pytest
import torch

# Ensure kernels directory is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kernels"))

from swizzle_kernels.paged_xor_attention import paged_xor_attention_decode, swizzle_smem_index
from swizzle_kernels.vllm_plugin import register


def test_xor_swizzle_bijection():
    # Verify that for each row, column indices [0..31] map to unique values in [0..31]
    for row in range(64):
        seen = set()
        for col in range(32):
            swizzled = col ^ (row >> 2)
            # In a 32-bank SRAM, the bank index is swizzled % 32
            bank_id = swizzled % 32
            seen.add(bank_id)
        # All 32 banks must be hit exactly once (zero bank collisions!)
        assert len(seen) == 32, f"Bank collision detected at row {row}!"


def test_swizzle_smem_index():
    idx = swizzle_smem_index(0, 0, tile_cols=64)
    assert idx == 0

    idx2 = swizzle_smem_index(4, 2, tile_cols=64)
    # row=4 >> 2 = 1. col=2 ^ 1 = 3. idx = 4*64 + 3 = 259
    assert idx2 == 259


def test_paged_xor_attention_forward():
    num_seqs = 2
    num_heads = 4
    head_dim = 64
    query = torch.randn(num_seqs, num_heads, head_dim)
    key_cache = torch.zeros(10, num_heads, head_dim // 8, 16, 8)
    value_cache = torch.zeros(10, num_heads, head_dim, 16)
    block_tables = torch.zeros(num_seqs, 4, dtype=torch.long)
    seq_lens = torch.tensor([10, 15], dtype=torch.long)

    out = paged_xor_attention_decode(
        query=query,
        key_cache=key_cache,
        value_cache=value_cache,
        block_tables=block_tables,
        seq_lens=seq_lens,
    )
    assert out.shape == query.shape
    assert not torch.isnan(out).any()


def test_vllm_plugin_register():
    success = register()
    assert success is True
