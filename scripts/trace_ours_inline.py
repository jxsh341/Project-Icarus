"""Inline reimplementation of our LIF loop for trace inspection.

Same equations and semantics as fly/dynamics/lif.py (post-fix: freeze + drop),
but with a deterministic 1 ms drive to the driven neuron (mirroring the Brian2
probe), and per-step v/g dumps for the target neuron. Used only to compare
trajectories against the Brian2 StateMonitor trace.
"""
import numpy as np

p_v0, p_vth, p_vrst = -52.0, -45.0, -52.0
t_mbr, tau_s, t_rfc, t_dly, w_syn = 20.0, 5.0, 2.2, 1.8, 0.275
dt = 0.1
kick = 68.75  # w_syn * f_poi, direct to v of driven neuron
w_edge = 50 * w_syn  # 13.75 mV synaptic kick (50 synapses)

n_steps = int(2000.0 / dt)
e_m = np.exp(-dt / t_mbr)
e_s = np.exp(-dt / tau_s)
c_gain = tau_s / (t_mbr - tau_s)

v = np.array([p_v0, p_v0])
g = np.array([0.0, 0.0])
last = np.array([-np.inf, -np.inf])
pending = []

spikes = [[], []]
trace = []
for step in range(n_steps):
    t = step * dt
    # deterministic drive: kick to v of neuron 0 at t = 1, 2, 3, ...
    if round(t, 6) == round(t) and round(t) >= 1:
        v[0] += kick
    frozen = (t - last) < (t_rfc - 1e-9)
    # deliver kicks
    new_pending = []
    for (tt, tgt, amt) in pending:
        if tt <= t + 1e-9:
            if not frozen[tgt]:
                g[tgt] += amt
        else:
            new_pending.append((tt, tgt, amt))
    pending = new_pending
    g_next = g * e_s
    u = v - p_v0
    u_next = e_m * u + c_gain * (e_m - e_s) * g
    g = np.where(frozen, g, g_next)
    v = np.where(frozen, p_v0 + u, p_v0 + u_next)
    can = (v > p_vth) & ~frozen
    for i in np.flatnonzero(can):
        spikes[i].append(round(t, 2))
        last[i] = t
        v[i] = p_vrst
        g[i] = 0.0
        pending.append((t + t_dly, 1, w_edge))
    if 6.0 <= t <= 10.5:
        trace.append((round(t, 2), v[0], g[0], v[1], g[1]))

print("driven neuron spikes (first 12):", spikes[0][:12])
print("target spikes (first 12):", spikes[1][:12], "| total:", len(spikes[1]))
t_t = spikes[1]
print("target ISIs (first 12):", [round(b - a, 2) for a, b in zip(t_t[:12], t_t[1:])])
print("\nours: t, v0, g0, v1, g1 over t=6.0..10.5:")
for row in trace:
    print(f"  t={row[0]:6.2f} v0={row[1]:9.3f} g0={row[2]:8.3f} v1={row[3]:9.3f} g1={row[4]:8.3f}")
