import math, re
from collections import Counter

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

def full_stats(words):
    H0, H1 = char_entropy(words)
    ttr = len(set(words))/len(words)
    avglen = sum(len(w) for w in words)/len(words)
    return dict(n=len(words), H0=H0, H1=H1, ttr=ttr, avglen=avglen)

with open('compare/culpeper_full.txt') as f:
    text = f.read()

# clean: lowercase, strip punctuation, split on whitespace
words = re.findall(r"[a-z']+", text.lower())
words = [w.strip("'") for w in words if w.strip("'")]

s = full_stats(words)
print("=== CULPEPER'S HERBAL (real 17th-c. English, herbal/recipe genre) ===")
print(f"n={s['n']} unique={len(set(words))} TTR={s['ttr']:.3f} avglen={s['avglen']:.2f}")
print(f"H0={s['H0']:.3f} bits/char   H1={s['H1']:.3f} bits/char")

print()
print("=== FULL COMPARISON TABLE ===")
print(f"{'Corpus':<28}{'N':>6}{'TTR':>7}{'AvgLen':>8}{'H0':>7}{'H1':>7}")
print(f"{'Culpeper herbal (real)':<28}{s['n']:>6}{s['ttr']:>7.3f}{s['avglen']:>8.2f}{s['H0']:>7.3f}{s['H1']:>7.3f}")
print(f"{'Shopping list (toy)':<28}{75:>6}{0.333:>7.3f}{5.63:>8.2f}{3.991:>7.3f}{2.499:>7.3f}")
print(f"{'Voynichese A (herbal)':<28}{7652:>6}{0.320:>7.3f}{3.92:>8.2f}{3.860:>7.3f}{2.728:>7.3f}")
print(f"{'Voynichese B (herbal)':<28}{4351:>6}{0.340:>7.3f}{4.33:>8.2f}{3.796:>7.3f}{2.420:>7.3f}")
print(f"{'English prose (generic)':<28}{'~':>6}{'0.4-0.6':>7}{'~4.5':>8}{'~4.1':>7}{'3.5-3.8':>7}")
