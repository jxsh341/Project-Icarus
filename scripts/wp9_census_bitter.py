"""Census bitter-only recruited neurons and overlap with sugar set."""
import json
from collections import Counter
from pathlib import Path

import numpy as np
from scipy import sparse

from fly.dynamics.lif import LIFParams, simulate_lif

base = Path('data/processed/neuprint_snapshots/run-007')
meta = {}
for p in sorted(base.glob('neurons_batch_*.json')):
    for r in json.loads(p.read_text(encoding='utf-8')):
        meta[r['bodyId']] = r

matrix = sparse.load_npz(base / 'connectivity_matrix_signed.npz').tocsr()
node_ids = np.load(base / 'connectivity_nodes.npy').tolist()
seeds = json.loads(Path('data/processed/neuprint_snapshots/wp6c_grn_seeds.json').read_text(encoding='utf-8'))
bitter = [r['bodyId'] for r in seeds['bitter_R']]

r = simulate_lif(matrix, node_ids, LIFParams(), duration_ms=1000.0,
                 stimulated=bitter, seed=8000)
recruited = list(r.spike_times.keys())
cls = Counter((meta[n].get('superclass') or '?') if n in meta else 'NOT_IN_META' for n in recruited)
typ = Counter((meta[n].get('type') or '?') if n in meta else '?' for n in recruited)
print('bitter-only recruited by superclass:', cls.most_common())
print('top types:', typ.most_common(15))
print('MN9_L 10331 in bitter-only recruited?', 10331 in recruited)

res = json.loads(Path('benchmarks_v2/sugar_recruitment/result.json').read_text(encoding='utf-8'))
sugar_spikers = set()
for t in res['per_trial']:
    sugar_spikers.update(int(k) for k, v in t['per_neuron_rates_hz'].items() if v > 0)
print(f'sugar-driven recruited set: {len(sugar_spikers)} neurons')
overlap = len(sugar_spikers.intersection(set(recruited)))
print(f'overlap sugar vs bitter-only recruited sets: {overlap} neurons')
