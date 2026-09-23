"""Census probe: what does Brian2's PoissonInput actually deliver?

Three parts on a minimal 1-neuron network (dt=0.1 ms, 2000 ms):
  A. Pure integrator (dv/dt = 0, no threshold), kick = 68.75 mV:
     final v / 68.75 = EXACT number of events drawn. A start-slot
     StateMonitor also gives the per-dt increment histogram (k distribution).
  B. Same integrator, but StateMonitor increments decoded: how many dt's
     got k=0,1,2,3 events.
  C. LIF driven neuron (rfc=0, threshold active, same kicks): spike count
     vs drawn events -> do any event-dt's fail to spike?
"""
from collections import Counter

import numpy as np
from brian2 import (
    Hz, Network, NeuronGroup, PoissonInput, SpikeMonitor, StateMonitor,
    defaultclock, mV, ms,
)

DT = 0.1 * ms
RUN = 2000 * ms
KICK = 68.75 * mV
RATE = 1000 * Hz

defaultclock.dt = DT

# ---- Part A/B: integrator census ----
integ = NeuronGroup(1, "dv/dt = 0 * volt/second : volt", method="euler")
integ.v = 0 * mV
poi_a = PoissonInput(integ, "v", N=1, rate=RATE, weight=KICK)
mon_a = StateMonitor(integ, "v", record=0)
net_a = Network(integ, poi_a, mon_a)
net_a.run(RUN)

v_a = np.asarray(mon_a[0].v / mV)
increments = np.diff(v_a)
increments = np.concatenate([[v_a[0]], increments])  # include t=0 sample? first sample is at t=0 before any delivery... keep simple:
increments = np.diff(v_a)
ks = np.round(increments / 68.75).astype(int)
hist = Counter(ks.tolist())
events_total = v_a[-1] / 68.75
print("A) integrator final v (mV):", v_a[-1])
print("A) TOTAL events drawn over 2000 ms:", events_total, "(nominal: 2000)")
print("B) per-dt event-count histogram:", dict(sorted(hist.items())))
lam = events_total / (RUN / DT)
print(f"B) implied lambda per dt: {lam:.5f} (nominal 0.1)")

# ---- Part C: LIF driven neuron ----
eqs = """
dv/dt = (v_0 - v + g) / t_mbr : volt (unless refractory)
dg/dt = -g / tau : volt (unless refractory)
rfc : second
"""
neu = NeuronGroup(
    1, eqs, method="linear", threshold="v > -45 * mV",
    reset="v = -52 * mV; g = 0 * mV", refractory="rfc",
    namespace={"v_0": -52 * mV, "t_mbr": 20 * ms, "tau": 5 * ms},
)
neu.v = -52 * mV
neu.g = 0 * mV
neu.rfc = 0 * ms  # mirror poi(): no refractory for driven neuron
poi_c = PoissonInput(neu, "v", N=1, rate=RATE, weight=KICK)
spk = SpikeMonitor(neu)
mon_c = StateMonitor(neu, "v", record=0)
net_c = Network(neu, poi_c, spk, mon_c)
net_c.run(RUN)

v_c = np.asarray(mon_c[0].v / mV)
inc_c = np.diff(v_c)
event_no_spike = np.flatnonzero(inc_c > 60)  # kick landed, v stayed elevated
print(f"\nC) LIF driven spikes: {spk.num_spikes} (reference run_trial gave ~1814)")
print(f"C) event-dt's with NO spike (v elevated): {len(event_no_spike)}")
if len(event_no_spike):
    print("   increments at those dt's (mV):", np.round(inc_c[event_no_spike], 2)[:12].tolist())
print(f"C) events drawn (part A) minus spikes: {events_total - spk.num_spikes}")
