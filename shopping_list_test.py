import math
from collections import Counter

# A real, plausible shopping list -- the kind of constrained, repetitive,
# domain-narrow English text your question is asking about.
shopping_list = """
milk eggs bread butter cheese apples bananas chicken rice pasta
tomatoes onions garlic olive oil salt pepper coffee tea sugar
milk bread eggs yogurt spinach carrots potatoes bananas apples
chicken beef pasta rice butter cheese tomatoes onions coffee
milk eggs bread bananas apples yogurt spinach carrots chicken
rice butter cheese tomatoes onions garlic salt pepper sugar tea
bread milk eggs apples bananas chicken beef pasta rice cheese
butter spinach carrots potatoes onions tomatoes coffee tea
""".split()

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
    first = Counter(w[0] for w in words)
    last = Counter(w[-1] for w in words)
    return dict(n=len(words), H0=H0, H1=H1, ttr=ttr, avglen=avglen, first=first, last=last)

s = full_stats(shopping_list)
print("=== SHOPPING LIST STATS ===")
print(f"n={s['n']} unique={len(set(shopping_list))} TTR={s['ttr']:.3f} avglen={s['avglen']:.2f}")
print(f"H0={s['H0']:.3f} bits/char   H1={s['H1']:.3f} bits/char")
print(f"Top initial letters: {s['first'].most_common(6)}")
print(f"Top final letters:   {s['last'].most_common(6)}")

print()
print("=== COMPARISON TABLE: Shopping list vs Voynichese A vs B vs real English prose ===")
print(f"{'Corpus':<22}{'TTR':>7}{'AvgLen':>8}{'H0':>7}{'H1':>7}")
print(f"{'Shopping list':<22}{s['ttr']:>7.3f}{s['avglen']:>8.2f}{s['H0']:>7.3f}{s['H1']:>7.3f}")
print(f"{'Voynichese A (herbal)':<22}{0.320:>7.3f}{3.92:>8.2f}{3.860:>7.3f}{2.728:>7.3f}")
print(f"{'Voynichese B (herbal)':<22}{0.340:>7.3f}{4.33:>8.2f}{3.796:>7.3f}{2.420:>7.3f}")
print(f"{'English prose (typical)':<22}{'~0.4-0.6':>7}{'~4.5':>8}{'~4.1':>7}{'~3.5-3.8':>7}")
