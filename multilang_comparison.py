import re, math
from collections import Counter

# ===== Gather all stats we've computed so far for each corpus, in one place =====
# Format: (TTR, H1_char_entropy, avg_word_len, sparse_compression_ratio)

# These come from our actual prior runs (recorded in README/findings)
profiles = {
    'Voynichese_A':         dict(ttr=0.320, h1=2.728, avglen=3.92, compress=1.20),
    'Voynichese_B':         dict(ttr=0.340, h1=2.420, avglen=4.33, compress=1.23),
    'Culpeper_English':     dict(ttr=0.304, h1=3.465, avglen=4.37, compress=1.153),
    'Carmina_Burana_Latin': dict(ttr=0.684, h1=3.098, avglen=5.37, compress=1.13),
    'Hebrew_Genesis':       dict(ttr=None, h1=None, avglen=None, compress=1.17),  # need to compute h1/ttr fresh
}

# Compute missing Hebrew stats fresh (we only had compression ratio before)
def char_entropy(words):
    corpus = ''.join(words)
    counts = Counter(corpus); total = sum(counts.values())
    H0 = -sum((c/total)*math.log2(c/total) for c in counts.values())
    bigrams = Counter(); ctx = Counter()
    for i in range(len(corpus)-1):
        a,b = corpus[i], corpus[i+1]
        bigrams[(a,b)] += 1; ctx[a] += 1
    H1 = 0.0
    for (a,b),cnt in bigrams.items():
        p_ab = cnt/total; p_b_given_a = cnt/ctx[a]
        H1 -= p_ab * math.log2(p_b_given_a)
    return H0, H1

with open('../compare/hebrew_genesis_sample.txt', encoding='utf-8') as f:
    text = f.read()
hebrew_words = re.findall(r"[\u05D0-\u05EA]+", text)
H0, H1 = char_entropy(hebrew_words)
ttr = len(set(hebrew_words))/len(hebrew_words)
avglen = sum(len(w) for w in hebrew_words)/len(hebrew_words)
profiles['Hebrew_Genesis'] = dict(ttr=ttr, h1=H1, avglen=avglen, compress=1.17)

print("=== FULL MULTI-METRIC PROFILE TABLE ===")
print(f"{'Corpus':<22}{'TTR':>8}{'H1':>8}{'AvgLen':>8}{'Compress':>10}")
for name, p in profiles.items():
    print(f"{name:<22}{p['ttr']:>8.3f}{p['h1']:>8.3f}{p['avglen']:>8.2f}{p['compress']:>10.3f}")

# ===== Normalize and compute Euclidean distance from each language to Voynichese A and B =====
# Normalize each metric to z-scores across all corpora (so no single metric with a big
# numeric range dominates the distance calculation)
metrics = ['ttr', 'h1', 'avglen', 'compress']
import statistics
means = {m: statistics.mean(p[m] for p in profiles.values()) for m in metrics}
stdevs = {m: statistics.pstdev(p[m] for p in profiles.values()) for m in metrics}

def zscore_vec(p):
    return {m: (p[m]-means[m])/stdevs[m] if stdevs[m] > 0 else 0 for m in metrics}

zvecs = {name: zscore_vec(p) for name, p in profiles.items()}

def euclidean(v1, v2):
    return math.sqrt(sum((v1[m]-v2[m])**2 for m in metrics))

print("\n=== DISTANCE FROM EACH REAL LANGUAGE TO VOYNICHESE (lower = more similar) ===")
for target in ['Voynichese_A', 'Voynichese_B']:
    print(f"\nDistances to {target}:")
    dists = []
    for name in profiles:
        if name == target or name.startswith('Voynichese'):
            continue
        d = euclidean(zvecs[target], zvecs[name])
        dists.append((d, name))
    for d, name in sorted(dists):
        print(f"  {name:<22} distance = {d:.3f}")
