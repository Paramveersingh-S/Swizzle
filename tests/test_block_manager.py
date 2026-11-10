import pytest
from swizzle.engine.sequence import Sequence
from swizzle.engine.block_manager import BlockManager


def test_block_manager_allocation_and_prefix_cache():
    bm = BlockManager(num_blocks=32, block_size=4, enable_prefix_cache=True)
    assert bm.num_free_blocks == 32

    # Seq 1: 8 tokens -> 2 blocks
    seq1 = Sequence(seq_id=1, prompt_tokens=[1, 2, 3, 4, 5, 6, 7, 8], block_size=4)
    bm.allocate(seq1)

    assert len(seq1.block_table) == 2
    assert bm.num_free_blocks == 30
    assert bm.prefix_cache_hits == 0

    # Seq 2: identical prefix of 8 tokens
    seq2 = Sequence(seq_id=2, prompt_tokens=[1, 2, 3, 4, 5, 6, 7, 8], block_size=4)
    bm.allocate(seq2)

    assert len(seq2.block_table) == 2
    # Both blocks should be reused from prefix cache!
    assert seq2.block_table == seq1.block_table
    assert bm.prefix_cache_hits == 2
    assert bm.num_free_blocks == 30  # No new physical blocks consumed!


def test_block_manager_append_slot_and_cow():
    bm = BlockManager(num_blocks=32, block_size=4, enable_prefix_cache=True)

    # Incomplete block (3 tokens out of 4)
    seq1 = Sequence(seq_id=1, prompt_tokens=[1, 2, 3], block_size=4)
    bm.allocate(seq1)

    # Fork seq2 from seq1 (e.g. beam search / best-of-n)
    seq2 = Sequence(seq_id=2, prompt_tokens=[1, 2, 3], block_size=4)
    bm.fork(seq1, seq2)

    # Shared block 0 has ref_count = 2
    shared_block_id = seq1.block_table[0]
    assert bm.blocks[shared_block_id].ref_count == 2
    assert seq1.block_table == seq2.block_table

    # Appending a slot to seq1 into a shared, non-full block triggers Copy-On-Write (COW)
    seq1.append_token_id(99)
    bm.append_slot(seq1)

    assert seq1.block_table[0] != seq2.block_table[0]
    assert bm.blocks[shared_block_id].ref_count == 1
    assert bm.blocks[seq1.block_table[0]].token_ids == [1, 2, 3, 99]
    assert bm.blocks[seq2.block_table[0]].token_ids == [1, 2, 3]


def test_ast_diff_virtual_paging_remap():
    bm = BlockManager(num_blocks=32, block_size=4)
    seq = Sequence(seq_id=1, prompt_tokens=list(range(16)), block_size=4)
    bm.allocate(seq)

    original_table = list(seq.block_table)
    assert len(original_table) == 4

    # Simulate AST reordering: function in block 3 moved to block 1
    ast_diff_map = {3: 1}
    remapped = bm.remap_ast_blocks(seq, ast_diff_map)

    assert remapped == 1
    assert seq.block_table[1] == original_table[3]
    assert bm.ast_cache_hits == 1


def test_block_manager_free():
    bm = BlockManager(num_blocks=16, block_size=4)
    seq = Sequence(seq_id=1, prompt_tokens=[1, 2, 3, 4, 5, 6, 7, 8], block_size=4)
    bm.allocate(seq)
    assert bm.num_free_blocks == 14

    bm.free(seq)
    assert len(seq.block_table) == 0
    assert bm.num_free_blocks == 16
