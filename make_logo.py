"""Brend nomidan oddiy logotip yaratadi. O'z logotipingiz bo'lsa, assets/logo.png ni almashtiring."""
import yaml, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
b = yaml.safe_load(open("config.yaml"))["brand"]
ini = "".join(w[0] for w in b["name"].replace("_", " ").split())[:2].upper() or b["name"][:2].upper()
fig = plt.figure(figsize=(2, 2), dpi=200); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
ax.add_patch(plt.Circle((0.5, 0.5), 0.48, color=b["color"]))
ax.text(0.5, 0.5, ini, ha="center", va="center", color="white", fontsize=48, fontweight="bold")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
fig.savefig(b["logo"], transparent=True); print("Logo:", b["logo"])
