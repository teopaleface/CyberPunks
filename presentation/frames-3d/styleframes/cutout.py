"""Cut the planet out of a concept plate whose background is a flat navy.
Keeps everything not connected to the border through near-background pixels."""
import sys
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

src, dst = sys.argv[1], sys.argv[2]
im = np.asarray(Image.open(src).convert("RGB")).astype(np.int16)
h, w, _ = im.shape
border = np.concatenate([im[:4].reshape(-1, 3), im[-4:].reshape(-1, 3), im[:, :4].reshape(-1, 3), im[:, -4:].reshape(-1, 3)])
bg = np.median(border, axis=0)
dist = np.sqrt(((im - bg) ** 2).sum(axis=2))
near = dist < float(sys.argv[3]) if len(sys.argv) > 3 else dist < 16
lab, n = ndimage.label(near)
edge_labels = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
sizes = ndimage.sum(near, lab, range(1, n + 1))
big = {i + 1 for i, sz in enumerate(sizes) if sz > (int(sys.argv[4]) if len(sys.argv) > 4 else 1500)}  # enclosed navy pockets (e.g. between wires)
outside = np.isin(lab, list(edge_labels | big))
alpha = (~outside).astype(np.uint8) * 255
# soft edge: feather with the colour distance near the boundary
soft = np.clip((dist - 6) / 14, 0, 1) * 255
edge = ndimage.binary_dilation(~outside, iterations=2) & ~ndimage.binary_erosion(~outside, iterations=2)
alpha = np.where(edge, np.maximum(alpha * 0, soft).astype(np.uint8), alpha)
a = Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(0.8))
out = Image.open(src).convert("RGBA"); out.putalpha(a)
out.save(dst)
print(dst, "bg", bg.tolist())
