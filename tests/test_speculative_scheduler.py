import pytest
from swizzle.engine.sequence import Sequence, SequenceGroup, SamplingParams
from swizzle.engine.block_manager import BlockManager
from swizzle.engine.speculative_scheduler import SpeculativeScheduler


def test_ngram_draft_candidates():
    bm = BlockManager(num_blocks=32, block_size=4)
    spec = SpeculativeScheduler(block_manager=bm, gamma=3, ngram_min_order=2)

    # Prompt with repeated pattern: [1, 2, 3, 4, 1, 2, 3] -> next should draft [4]
    seq = Sequence(seq_id=1, prompt_tokens=[1, 2, 3, 4, 10, 20, 1, 2, 3], block_size=4)
    bm.allocate(seq)

    drafts = spec.draft_candidates_ngram(seq)
    assert len(drafts) > 0
    assert drafts[0] == 4


def test_speculative_verification_and_commit():
    bm = BlockManager(num_blocks=32, block_size=4)
    spec = SpeculativeScheduler(block_manager=bm, gamma=3)

    seq = Sequence(seq_id=1, prompt_tokens=[1, 2, 3, 4], block_size=4)
    bm.allocate(seq)

    group = SequenceGroup("req-spec", [seq], SamplingParams())
    drafts = spec.prepare_drafts([group])
    assert len(drafts) == 1

    draft = drafts[0]
    # Simulate target model agreeing with the first token of the draft
    target_preds = [draft.draft_tokens[0]]

    initial_len = seq.get_len()
    res = spec.verify_drafts(draft, seq, target_preds)

    assert res.num_accepted == 1
    assert seq.get_len() == initial_len + 1

    stats = spec.get_stats()
    assert stats["total_accepted"] == 1
    assert stats["acceptance_rate"] > 0.0
