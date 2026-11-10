import pytest
from swizzle.engine.sequence import Sequence
from swizzle.engine.block_manager import BlockManager
from swizzle.engine.disagg_coordinator import DisaggCoordinator


def test_disagg_coordinator_transfer():
    bm = BlockManager(num_blocks=32, block_size=4)
    coord = DisaggCoordinator(bandwidth_gbps=100.0)

    seq = Sequence(seq_id=1, prompt_tokens=list(range(64)), block_size=4)
    bm.allocate(seq)

    pkg = coord.transfer_kv_to_decode(seq, "req-pd-1")

    assert pkg.request_id == "req-pd-1"
    assert pkg.prompt_len == 64
    assert pkg.num_blocks == 16
    assert pkg.transfer_time_ms > 0
    # On a 100 Gbps network, transferring 64 tokens (~33 MB) should be sub-5 ms
    assert pkg.transfer_time_ms < 10.0

    stats = coord.get_stats()
    assert stats["total_transfers"] == 1
    assert stats["rdma_bandwidth_gbps"] == 100.0

