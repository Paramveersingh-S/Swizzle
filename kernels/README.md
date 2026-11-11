# Swizzle-Kernels

Hardware-roofline bitwise XOR shared-memory swizzled PagedAttention kernels.

## Overview
Eliminates 32-way shared memory bank conflicts on Ampere (sm_80), Ada (sm_89), and Hopper (sm_90) architectures using coordinate permutation:
$$\text{col}_{\text{swizzled}} = \text{col} \oplus (\text{row} \gg 2)$$

## vLLM Out-of-Tree Plugin
Install as a vLLM plugin:
```bash
pip install swizzle-kernels
```
vLLM will automatically discover the entry point via `[project.entry-points."vllm.general_plugins"]`.
