import re, math, random
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

with open('compare/carmina_burana.txt') as f:
    text = f.read()
words = re.findall(r"[a-z]+", text.lower())

s = full_stats(words)
print("=== CARMINA BURANA (real 13th-c. Latin, O Fortuna + In Taberna) ===")
print(f"n={s['n']} unique={len(set(words))} TTR={s['ttr']:.3f} avglen={s['avglen']:.2f}")
print(f"H0={s['H0']:.3f}  H1={s['H1']:.3f}")

# doubling rate -- treat each SENTENCE (period-delimited) as a line unit,
# but ALSO check the comma-delimited clause level since the "Bibit..." litany
# is comma-separated within one long sentence
sentences = re.split(r'[.]+', text)
lines = []
for sent in sentences:
    w = re.findall(r"[a-z]+", sent.lower())
    if w:
        lines.append(w)

def immediate_repeat_stats(lines):
    total = 0; reps = 0; examples = []
    for line in lines:
        for i in range(len(line)-1):
            total += 1
            if line[i] == line[i+1]:
                reps += 1
                examples.append(line[i])
    return reps, total, (reps/total if total else 0), examples

def expected_repeat_rate(lines):
    flat = [w for line in lines for w in line]
    counts = Counter(flat); n = len(flat)
    return sum((c/n)**2 for c in counts.values())

def shuffled_repeat_rate(lines, seed=42, n_trials=30):
    rng = random.Random(seed)
    flat = [w for line in lines for w in line]
    lens = [len(l) for l in lines]
    rates = []
    for _ in range(n_trials):
        shuf = flat[:]; rng.shuffle(shuf)
        idx=0; reps=0; pairs=0
        for ln in lens:
            seg = shuf[idx:idx+ln]; idx+=ln
            for i in range(len(seg)-1):
                pairs+=1
                if seg[i]==seg[i+1]: reps+=1
        rates.append(reps/pairs if pairs else 0)
    return sum(rates)/len(rates)

reps, total, rate, examples = immediate_repeat_stats(lines)
expected = expected_repeat_rate(lines)
shuf = shuffled_repeat_rate(lines)

print(f"\n=== DOUBLING RATE (sentence-bounded) ===")
print(f"Real rate: {rate*100:.3f}% ({reps}/{total})")
print(f"Chance baseline (freq^2): {expected*100:.3f}%")
print(f"Shuffled baseline: {shuf*100:.3f}%")
print(f"Examples of real doublings: {examples}")
if shuf > 0:
    print(f"Real/Shuffled ratio: {rate/shuf:.2f}x")
else:
    print("Real/Shuffled ratio: undefined (shuffled rate is 0)")

print("\n=== FULL COMPARISON TABLE ===")
print(f"{'Corpus':<28}{'TTR':>7}{'H1':>7}{'Doubl rate':>11}{'Shuf base':>10}{'Ratio':>7}")
print(f"{'Carmina Burana (real)':<28}{s['ttr']:>7.3f}{s['H1']:>7.3f}{rate*100:>10.3f}%{shuf*100:>9.3f}%{(rate/shuf if shuf else float('nan')):>6.2f}x")
print(f"{'Culpeper (real prose)':<28}{0.304:>7.3f}{3.465:>7.3f}{0.000:>10.3f}%{1.569:>9.3f}%{0.00:>6.2f}x")
print(f"{'Voynichese A':<28}{0.320:>7.3f}{2.728:>7.3f}{1.155:>10.3f}%{0.587:>9.3f}%{1.97:>6.2f}x")
print(f"{'Voynichese B':<28}{0.340:>7.3f}{2.420:>7.3f}{1.010:>10.3f}%{0.502:>9.3f}%{2.01:>6.2f}x")
