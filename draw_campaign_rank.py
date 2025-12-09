import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# load csv
df = pd.read_csv("campaign_csv/campaign_rank_2025.csv")

# compute normalized RR*
def compute_rr(df, rank_col):
    return 1 - (df[rank_col] - 1) / (df["Number of Participants"] - 1)

df["RR_Precision"] = compute_rr(df, "Precision Rank")
df["RR_Recall"]    = compute_rr(df, "Recall Rank")
df["RR_F1"]        = compute_rr(df, "F1 Rank")

# compute MRR* (mean RR*)
mrr_precision = df["RR_Precision"].mean()
mrr_recall    = df["RR_Recall"].mean()
mrr_f1        = df["RR_F1"].mean()

# setup figure
tracks = df["Track Name"]
x = np.arange(len(tracks))
colors = plt.get_cmap("tab10").colors
offset = 0.25

fig, ax = plt.subplots(figsize=(10, 6))

# draw RR*
# precision
p_rr = ax.vlines(x - offset, 0, df["RR_Precision"], color=colors[0], linewidth=2)
p_dot = ax.scatter(x - offset, df["RR_Precision"], color=colors[0], s=60)
# recall
r_rr = ax.vlines(x, 0, df["RR_Recall"], color=colors[1], linewidth=2)
r_dot = ax.scatter(x, df["RR_Recall"], color=colors[1], s=60)
# f1 score
f_rr = ax.vlines(x + offset, 0, df["RR_F1"], color=colors[2], linewidth=2)
f_dot = ax.scatter(x + offset, df["RR_F1"], color=colors[2], s=60)

# draw MRR*
p_mrr_line = ax.axhline(mrr_precision, color=colors[0], linestyle="--", linewidth=2)
r_mrr_line = ax.axhline(mrr_recall,    color=colors[1], linestyle="--", linewidth=2)
f_mrr_line = ax.axhline(mrr_f1,        color=colors[2], linestyle="--", linewidth=2)

# legend order
legend_handles = [
    p_dot,                                  # RR Precision
    p_mrr_line,                             # MRR Precision
    r_dot,                                  # RR Recall
    r_mrr_line,                             # MRR Recall
    f_dot,                                  # RR F1
    f_mrr_line                              # MRR F1
]

legend_labels = [
    "RR* - Precision",
    f"MRR* = {mrr_precision:.4f}",
    "RR* - Recall",
    f"MRR* = {mrr_recall:.4f}",
    "RR* - F1 Score",
    f"MRR* = {mrr_f1:.4f}"
]

ax.legend(
    legend_handles,
    legend_labels,
    fontsize=10,
    loc="upper right"
)

# axis formatting
ax.set_xlabel("Track Name", fontsize=12)
ax.set_ylabel("Normalized Reciprocal Rank (RR*)", fontsize=12)

ax.set_xticks(x)
ax.set_xticklabels(tracks, fontsize=12, rotation=0)
ax.tick_params(axis='x', length=0)

ax.tick_params(axis='y', labelsize=12)
ax.set_ylim(0, 1.05)

ax.grid(False)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# save figure
plt.tight_layout()
plt.savefig(
    "campaign_figure/campaign-rank-2025.png",
    bbox_inches='tight',
    pad_inches=0.1
)

# show figure
plt.show()