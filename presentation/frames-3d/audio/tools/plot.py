"""Draw the film audio timeline (mix waveform, VO, music bed level, lines, beats) to timeline.png."""
import sys, json, numpy as np, soundfile as sf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
root = sys.argv[1]
T = json.load(open(f"{root}/timing.json"))
mix, sr = sf.read(f"{root}/local/daybreak_mix.wav"); vo, _ = sf.read(f"{root}/vo/vo_af_heart.wav"); sfx, _ = sf.read(f"{root}/sfx_stem.wav")
def env(x, hop=480):
    x = x.mean(1) if x.ndim > 1 else x; n = len(x) // hop
    return np.arange(n) * hop / sr, 20 * np.log10(np.sqrt((x[: n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-6)
fig, ax = plt.subplots(2, 1, figsize=(22, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1.3]})
bg = "#000F1E"; fig.patch.set_facecolor(bg)
for a in ax: a.set_facecolor(bg); a.tick_params(colors="#9fb3c8"); [s.set_color("#33475b") for s in a.spines.values()]
bed, _ = sf.read(f"{root}/local/music_bed_ducked.wav")
t, m = env(mix, 4800); t2, v = env(vo, 4800); _, music = env(bed, 4800)
ax[0].fill_between(t, -60, m, color="#163FE8", alpha=0.35, label="mix")
ax[0].plot(t, music, color="#00A3E0", lw=1, label="music bed, ducked (100 ms RMS)")
ax[0].plot(t2, v, color="#FA4616", lw=1, label="VO")
ax[0].set_ylim(-50, -5); ax[0].set_ylabel("RMS dBFS (100 ms)", color="#9fb3c8")
for b in T["music"]["beats"]:
    ax[0].axvline(b["t"], color="#ffffff", alpha=0.18 if b["downbeat"] else 0.06, lw=1)
ax[0].axvline(T["music"]["drop"], color="#FA4616", lw=2); ax[0].text(T["music"]["drop"] + 0.1, -5, "DROP", color="#FA4616", fontsize=11, weight="bold")
ax[0].axvline(T["music"]["button"], color="#00A3E0", lw=2); ax[0].text(T["music"]["button"] + 0.1, -5, "button", color="#00A3E0", fontsize=10)
for e in T["music"]["edits"]: ax[0].axvline(e["film_s"], color="#ffd400", lw=1, ls="--")
for x in T["sfx"]:
    tt = x.get("t", x.get("start")); ax[0].plot([tt], [-50], marker="v", color="#ffd400", ms=7)
ax[0].legend(loc="lower right", facecolor=bg, labelcolor="#cfe0f0", fontsize=9)
for l in T["lines"]:
    ax[1].add_patch(plt.Rectangle((l["start"], 0.15), l["end"] - l["start"], 0.7, color="#FA4616", alpha=0.85))
    ax[1].text(l["start"] + 0.05, 0.5, f'{l["index"]}', color="white", fontsize=11, va="center", weight="bold")
    for w in l["words"]: ax[1].plot([w["start"], w["start"]], [0.15, 0.3], color="white", lw=0.8)
    ax[1].text(l["start"], -0.25, f'{l["start"]:.2f}', color="#9fb3c8", fontsize=8)
ax[1].set_ylim(-0.5, 1); ax[1].set_yticks([]); ax[1].set_xlim(0, T["total_duration"]); ax[1].set_xticks(np.arange(0, T["total_duration"] + 1, 2))
ax[1].set_xlabel("film seconds", color="#9fb3c8")
fig.suptitle(f'Daybreak film audio - af_heart - total {T["total_duration"]:.2f} s - drop {T["music"]["drop"]:.3f} s - 77 BPM', color="white", fontsize=13)
plt.tight_layout(); plt.savefig(f"{root}/timeline.png", dpi=90, facecolor=bg)
