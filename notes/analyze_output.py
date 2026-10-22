"""Evidence gathering for inspection.md Q1-Q9."""
import json
from collections import defaultdict

with open("notes/words_pymupdf.json", encoding="utf-8") as f:
    mu = json.load(f)
with open("notes/words_pdfplumber.json", encoding="utf-8") as f:
    pb = json.load(f)
with open("notes/drawings.json", encoding="utf-8") as f:
    drw = json.load(f)

print(f"PyMuPDF words: {len(mu)}, pdfplumber words: {len(pb)}")
print()

# --- Q1: tokenization comparison ---
print("=== Q1: MU first 16 words (sorted by y0 then x0) ===")
mu_sorted = sorted(mu, key=lambda w: (round(w["y0"]), w["x0"]))
for w in mu_sorted[:16]:
    print(f"  {w['text']!r:35s}  x0={w['x0']:7.2f}  y0={w['y0']:7.2f}")
print()
print("=== Q1: PB first 16 words ===")
pb_sorted = sorted(pb, key=lambda w: (round(w["y0"]), w["x0"]))
for w in pb_sorted[:16]:
    print(f"  {w['text']!r:35s}  x0={w['x0']:7.2f}  y0={w['y0']:7.2f}")
print()

# --- Q2: special characters ---
special_chars = ["\u25b3", "\uff0d", "\uff08", "\uff09"]
print("=== Q2: Special characters in MU ===")
for w in mu:
    if any(c in w["text"] for c in special_chars):
        print(f"  {w['text']!r:35s}  x0={w['x0']:7.2f}  x1={w['x1']:7.2f}")
print()
print("=== Q2: Sample numeric tokens in MU ===")
for w in mu:
    if "," in w["text"] and w["x0"] > 200:
        print(f"  {w['text']!r:30s}  x0={w['x0']:7.2f}  x1={w['x1']:7.2f}")
        if sum(1 for ww in mu if "," in ww["text"] and ww["x0"] > 200) > 3:
            break
print()

# --- Row clustering (for Q3, Q4, Q5, Q6) ---
def y_mid(w):
    return (w["y0"] + w["y1"]) / 2

tagged = [(y_mid(w), w) for w in mu]
tagged.sort(key=lambda t: t[0])
rows = []
cur_mids = [tagged[0][0]]
cur_words = [tagged[0][1]]
for ym, w in tagged[1:]:
    cm = sum(cur_mids) / len(cur_mids)
    if abs(ym - cm) <= 3.0:
        cur_mids.append(ym)
        cur_words.append(w)
    else:
        rows.append({"y_mid": sum(cur_mids) / len(cur_mids),
                     "words": sorted(cur_words, key=lambda x: x["x0"])})
        cur_mids = [ym]
        cur_words = [w]
rows.append({"y_mid": sum(cur_mids) / len(cur_mids),
             "words": sorted(cur_words, key=lambda x: x["x0"])})

# --- Q3: check for split rows ---
print("=== Q3: Row y-spread check ===")
for i, row in enumerate(rows):
    ws = row["words"]
    y_mids = [(w["y0"] + w["y1"]) / 2 for w in ws]
    spread = max(y_mids) - min(y_mids) if len(y_mids) > 1 else 0
    if spread > 2:
        print(f"  Row {i+1}  y_mid={row['y_mid']:.2f}  spread={spread:.2f}  "
              f"words={[w['text'] for w in ws]}")
print()

# --- Q4: numeric column positions ---
print("=== Q4: Numeric token x0 and x1 (x0>250) ===")
num_toks = [(w["x0"], w["x1"], w["text"]) for w in mu
            if any(c.isdigit() for c in w["text"]) and w["x0"] > 250]
# Cluster x0 values
x0s = sorted(set(round(x[0]) for x in num_toks))
x1s = sorted(set(round(x[1]) for x in num_toks))
print(f"  Distinct x0 (rounded): {x0s}")
print(f"  Distinct x1 (rounded): {x1s}")
# Column grouping
prev_yr = [t for t in num_toks if t[0] < 430]
curr_yr = [t for t in num_toks if t[0] >= 430]
if prev_yr:
    print(f"  Prev-yr col: x0 range [{min(t[0] for t in prev_yr):.1f}, "
          f"{max(t[0] for t in prev_yr):.1f}]  x1 range "
          f"[{min(t[1] for t in prev_yr):.1f}, {max(t[1] for t in prev_yr):.1f}]")
if curr_yr:
    print(f"  Curr-yr col: x0 range [{min(t[0] for t in curr_yr):.1f}, "
          f"{max(t[0] for t in curr_yr):.1f}]  x1 range "
          f"[{min(t[1] for t in curr_yr):.1f}, {max(t[1] for t in curr_yr):.1f}]")
print()

# --- Q5: label x0 positions ---
print("=== Q5: Label left-edge (x0) distribution ===")
label_words = [w for w in mu if w["x0"] < 250]
x0_counts = defaultdict(list)
for w in label_words:
    x0_counts[round(w["x0"])].append(w["text"])
for x0, texts in sorted(x0_counts.items()):
    examples = list(dict.fromkeys(texts))[:3]
    print(f"  x0={x0:4d}  n={len(texts):3d}  e.g. {examples}")
print()

# --- Q6: header vs data rows ---
header_rows = []
data_rows = []
for row in rows:
    has_num = any(any(c.isdigit() for c in w["text"]) and w["x0"] > 200
                  for w in row["words"])
    if has_num:
        data_rows.append(row)
    else:
        header_rows.append(row)

print(f"=== Q6: rows with numbers={len(data_rows)}, without={len(header_rows)} ===")
print("Header/section rows:")
for r in header_rows:
    first_x0 = r["words"][0]["x0"] if r["words"] else 0
    text = " | ".join(w["text"] for w in r["words"])
    print(f"  y={r['y_mid']:7.2f}  x0={first_x0:6.2f}  {text}")
print()

# --- Q7: drawings ---
print("=== Q7: Drawing analysis ===")
item_types = defaultdict(int)
thin_rects = []
thick_rects = []
shaded = []
for d in drw:
    for item in d["items"]:
        item_types[item["type"]] += 1
        if item["type"] == "rect":
            h = item["y1"] - item["y0"]
            if h < 1.0:
                thin_rects.append((item, d["fill"]))
            elif h > 10:
                thick_rects.append((item, d["fill"]))
            fill = d["fill"]
            if fill not in ["(0.0, 0.0, 0.0)", "(1.0, 1.0, 1.0)", "None"]:
                shaded.append((item, fill))
print(f"  Item types: {dict(item_types)}")
fills = defaultdict(int)
for d in drw:
    fills[d["fill"]] += 1
print(f"  Fill colors: {dict(fills)}")
print(f"  Thin rects (h<1): {len(thin_rects)}")
print(f"  Thick rects (h>10): {len(thick_rects)}")
print(f"  Shaded (non-B/W fill): {len(shaded)}")
if thin_rects:
    print(f"  Thin rect example: {thin_rects[0][0]}  fill={thin_rects[0][1]}")
if shaded:
    print(f"  Shaded rect example: {shaded[0][0]}  fill={shaded[0][1]}")
print()

# --- Q8: header positions ---
print("=== Q8: Page header words (y0 < 145) ===")
for w in sorted(mu, key=lambda x: (x["y0"], x["x0"])):
    if w["y0"] < 145:
        print(f"  {w['text']!r:35s}  x0={w['x0']:7.2f}  y0={w['y0']:7.2f}  y1={w['y1']:7.2f}")
body_start_y = min(w["y0"] for w in mu if w["y0"] > 145 and w["x0"] < 200)
print(f"  Table body first label at y0={body_start_y:.2f}")
header_end_y = max(w["y1"] for w in mu if w["y0"] < 145)
print(f"  Header ends at y1={header_end_y:.2f}")
print(f"  Gap header→body: {body_start_y - header_end_y:.2f} pt")
