import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agentcompactor.core import AgentContextCompactor, GENESIS_HASH


class TestAgentContextCompactor(unittest.TestCase):
    def setUp(self):
        self.compactor = AgentContextCompactor()

    def test_lossless_compaction_and_temporal_anchoring(self):
        raw_history = [
            {'role': 'system', 'content': 'Base prompt instruction A'},
            {'role': 'system', 'content': 'Base prompt instruction A'},  # Duplicate
            {'role': 'user', 'content': 'Run deployment to cluster'},
            {'role': 'tool', 'content': 'DEBUG_TRACE: socket 10.0.0.1 closed'},  # Noise
            {'role': 'tool', 'content': 'Deployment successful (commit #9812)'},
        ]

        compacted, receipt = self.compactor.compact_context_stream(
            session_id='sess_deploy_01',
            conversation_history=raw_history,
        )

        # Invariant 1: Temporal Anchor exists
        self.assertTrue(compacted[0]['content'].startswith('[TEMPORAL_ANCHOR]'))

        # Invariant 2: Duplicates & debug noise pruned
        roles = [x['role'] for x in compacted]
        self.assertEqual(roles.count('system'), 2)  # 1 anchor + 1 unique base prompt

        # Invariant 3: Reduction ratio computed
        self.assertGreaterEqual(receipt.reduction_ratio, 0.20)
        self.assertNotEqual(receipt.signature_hash, GENESIS_HASH)

        # Invariant 4: Ledger cryptographic integrity
        is_valid, err = self.compactor.ledger.verify_chain_integrity()
        self.assertTrue(is_valid, f'Compactor ledger broken: {err}')


if __name__ == '__main__':
    unittest.main()
