import re, math, random
from collections import Counter

def char_entropy(words):
    corpus = ''.join(words)
    counts = Counter(corpus); total = sum(counts.values())
    if total == 0: return 0, 0
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

def build_dictionary_fast(words, max_atoms=25, min_atom_len=2, max_atom_len=5,
                          candidate_min_freq=8, top_k=80):
    candidates = Counter()
    for w in words:
        n = len(w)
        for L in range(min_atom_len, max_atom_len+1):
            for i in range(n-L+1):
                candidates[w[i:i+L]] += 1
    candidates = {a:c for a,c in candidates.items() if c >= candidate_min_freq}
    scored = sorted(candidates.items(), key=lambda kv: -(kv[1]*(len(kv[0])-1)))
    pool = sorted([a for a,c in scored[:top_k]], key=lambda a: (-len(a), -candidates[a]))
    return pool[:max_atoms]

def encode_with_dict(word, dict_sorted):
    n = len(word); atoms = []; i = 0
    while i < n:
        matched = None
        for atom in dict_sorted:
            L = len(atom)
            if i+L <= n and word[i:i+L] == atom:
                matched = atom; break
        if matched:
            atoms.append(matched); i += len(matched)
        else:
            atoms.append(word[i]); i += 1
    return atoms

def compression_ratio(words, min_freq=6):
    unique = list(set(words))
    d = build_dictionary_fast(unique, candidate_min_freq=min_freq)
    ds = sorted(d, key=len, reverse=True)
    total_atoms = sum(len(encode_with_dict(w, ds)) for w in unique)
    total_chars = sum(len(w) for w in unique)
    return total_chars/total_atoms if total_atoms else 1.0

def doubling_rate_and_ratio(words):
    """Treat the word list as one continuous sequence for doubling.
    For liturgical texts we don't have line structure so this is approximate."""
    pairs = len(words)-1
    reps = sum(1 for i in range(pairs) if words[i]==words[i+1])
    rate = reps/pairs if pairs else 0
    # chance baseline = sum of p_i^2
    counts = Counter(words); n = len(words)
    chance = sum((c/n)**2 for c in counts.values())
    ratio = rate/chance if chance > 0 else float('nan')
    return reps, pairs, rate, chance, ratio

def run_corpus(words, label, min_freq=6):
    H0, H1 = char_entropy(words)
    ttr = len(set(words))/len(words)
    avglen = sum(len(w) for w in words)/len(words)
    compress = compression_ratio(words, min_freq=min_freq)
    reps, pairs, rate, chance, ratio = doubling_rate_and_ratio(words)
    print(f"\n{label}:")
    print(f"  n={len(words)} unique={len(set(words))} TTR={ttr:.3f} avglen={avglen:.2f}")
    print(f"  H0={H0:.3f} H1={H1:.3f} compress={compress:.3f}x")
    print(f"  Doubling: {reps}/{pairs} = {rate*100:.3f}% (chance={chance*100:.3f}%, ratio={ratio:.2f}x)")
    return dict(label=label, n=len(words), ttr=ttr, h1=H1, avglen=avglen,
                compress=compress, doubling_ratio=ratio)

# Load new corpora
with open('../compare/rigveda_sample.txt', encoding='utf-8') as f:
    rigveda = f.read().split()

with open('../compare/hebrew_liturgical.txt', encoding='utf-8') as f:
    hebrew_liturgy = f.read().split()

# Use a sample of Rigveda comparable in size to other corpora for fair comparison
# but also show full-corpus numbers
print("=== EXTENDED MULTI-LANGUAGE ANALYSIS: RIGVEDA + HEBREW LITURGY ===")
results = []
results.append(run_corpus(rigveda[:5000], "Rigveda sample (5,000 words)", min_freq=5))
results.append(run_corpus(rigveda, "Rigveda FULL (135,279 words)", min_freq=20))
results.append(run_corpus(hebrew_liturgy, "Hebrew Hallel/Liturgical Psalms 113-150", min_freq=4))

print("\n=== REFERENCE POINTS (from prior analysis) ===")
print(f"  Voynichese A:        H1=2.726  compress=1.200x  doubling_ratio=1.81x")
print(f"  Voynichese B:        H1=2.442  compress=1.230x  doubling_ratio=2.07x")
print(f"  Culpeper English:    H1=3.465  compress=1.153x  doubling_ratio=0.00x")
print(f"  Carmina Burana:      H1=3.098  compress=1.130x  doubling_ratio=0.00x")
print(f"  Hebrew Genesis:      H1=3.687  compress=1.162x")
print(f"  Arabic Al-Baqarah:   H1=3.843  compress=1.103x  doubling_ratio=0.00x")
