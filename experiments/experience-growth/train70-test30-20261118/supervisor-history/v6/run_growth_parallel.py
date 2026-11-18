"""Explicit scheduling amendment; inherit all frozen solver/training behavior."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import run_growth as frozen
from temporal_contract_analyzer.balance_budget import BalanceBudget


class ParallelRun(frozen.Run):
    def __init__(self, run_id):
        self.scheduler_ready = threading.Event()
        super().__init__(run_id, False)
        try:
            self.amendment = frozen.read(self.root/'scheduler-amendment.json')
            assert self.amendment['run_id'] == run_id
            assert self.amendment['original_manifest_sha256'] == frozen.file_sha(self.root/'manifest.json')
            for name, digest in self.amendment['scheduler_bindings'].items():
                assert frozen.file_sha(frozen.HERE/name) == digest, name
            assert self.amendment['from_checkpoint'] == 20
            assert self.amendment['testing_workers'] == 4
            self.budget = BalanceBudget(self.root/'balance.json',authorized_total_cny=None,
                                       max_inflight_stages=4,max_requests=30000)
            self.budget.summary()  # Validate the sealed amended ledger before any dispatch.
            self.event('scheduler_amendment_loaded',amendment_sha256=frozen.file_sha(self.root/'scheduler-amendment.json'),
                       testing_workers=4,from_checkpoint=20,training_workers=1)
        except BaseException:
            self.stopping.set()
            self.writer.close()
            raise
        finally:
            self.scheduler_ready.set()

    def _heartbeats(self):
        self.scheduler_ready.wait()
        super()._heartbeats()

    def test_checkpoint(self, n):
        self.checkpoint='M'+str(n)
        path=self.root/'checkpoints'/(self.checkpoint+'.json')
        snapshot=frozen.read(path) if path.exists() else frozen.immutable(path,frozen.delegated_review.freeze(self.store))
        if n==0 and snapshot['entries']:raise frozen.EvidenceError('M0 must have no guidance')
        workers=4 if n>=20 else 2
        self.event('checkpoint_frozen',checkpoint=n,snapshot_sha256=snapshot['sha256'],entries=len(snapshot['entries']),
                   testing_workers=workers,scheduler_amendment_sha256=frozen.file_sha(self.root/'scheduler-amendment.json'))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures=[pool.submit(self.job,row,'testing',n,snapshot) for row in self.testing]
            try:
                for future in as_completed(futures):future.result()
            except BaseException:
                self.stopping.set()
                for future in futures:future.cancel()
                raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id',required=True)
    ParallelRun(parser.parse_args().run_id).execute()
