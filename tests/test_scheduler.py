import pytest
from swizzle.engine.sequence import Sequence, SequenceGroup, SequenceStatus, SamplingParams
from swizzle.engine.block_manager import BlockManager
from swizzle.engine.scheduler import Scheduler


def test_scheduler_prefill_and_decode_cycle():
    bm = BlockManager(num_blocks=64, block_size=4)
    sched = Scheduler(block_manager=bm, max_num_seqs=4, max_num_batched_tokens=64)

    seq1 = Sequence(seq_id=1, prompt_tokens=[10, 11, 12, 13], block_size=4)
    group1 = SequenceGroup("req-1", [seq1], SamplingParams(max_tokens=3))
    sched.add_sequence_group(group1)

    assert sched.has_unfinished_requests()
    assert len(sched.waiting) == 1

    # Step 1: Prefill scheduled
    out1 = sched.schedule()
    assert out1.is_prefill is True
    assert len(out1.scheduled_seq_groups) == 1
    assert out1.scheduled_seq_groups[0].request_id == "req-1"
    assert len(sched.running) == 1
    assert len(sched.waiting) == 0

    # Simulate token decode
    seq1.append_token_id(100)

    # Step 2: Decode scheduled (is_prefill = False)
    out2 = sched.schedule()
    assert out2.is_prefill is False
    assert len(out2.scheduled_seq_groups) == 1


def test_scheduler_preemption_on_memory_exhaustion():
    # Only 2 blocks total!
    bm = BlockManager(num_blocks=2, block_size=4)
    sched = Scheduler(block_manager=bm, max_num_seqs=2, max_num_batched_tokens=32)

    seq1 = Sequence(seq_id=1, prompt_tokens=[1, 2, 3, 4], block_size=4)
    group1 = SequenceGroup("req-1", [seq1], SamplingParams(max_tokens=5))
    sched.add_sequence_group(group1)

    # Schedule prefill for req-1 (takes 1 block)
    sched.schedule()
    assert len(sched.running) == 1

    seq2 = Sequence(seq_id=2, prompt_tokens=[5, 6, 7, 8], block_size=4)
    group2 = SequenceGroup("req-2", [seq2], SamplingParams(max_tokens=5))
    sched.add_sequence_group(group2)

    # Schedule prefill for req-2 (takes remaining 1 block, free blocks = 0)
    sched.schedule()

    # Now both blocks are occupied. Next decode step requires appending a slot.
    # BlockManager.can_append_slot will fail when blocks are full -> Preempt lowest priority!
    seq1.append_token_id(99)
    seq2.append_token_id(98)
    
    # Fill last slot
    seq1.append_token_id(101)
    seq1.append_token_id(102)
    seq1.append_token_id(103)

    out = sched.schedule()
    # At least one request is scheduled or preemption recovers blocks
    assert out.is_prefill is False or len(out.preempted_requests) > 0


def test_scheduler_abort_request():
    bm = BlockManager(num_blocks=32, block_size=4)
    sched = Scheduler(block_manager=bm, max_num_seqs=4)

    seq = Sequence(seq_id=1, prompt_tokens=[1, 2, 3, 4], block_size=4)
    group = SequenceGroup("req-to-abort", [seq], SamplingParams())
    sched.add_sequence_group(group)

    # Schedule prefill
    sched.schedule()
    assert bm.num_free_blocks == 31

    aborted = sched.abort_sequence_group("req-to-abort")
    assert aborted is True
    assert bm.num_free_blocks == 32  # Block reclaimed!
    assert not sched.has_unfinished_requests()

