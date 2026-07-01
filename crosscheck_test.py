import re, math
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

def build_dictionary_fast(words, max_atoms=25, min_atom_len=2, max_atom_len=5, candidate_min_freq=6, top_k_candidates=80):
    candidates = Counter()
    for w in words:
        n = len(w)
        for L in range(min_atom_len, max_atom_len+1):
            for i in range(n - L + 1):
                candidates[w[i:i+L]] += 1
    candidates = {a: c for a, c in candidates.items() if c >= candidate_min_freq}
    scored = sorted(candidates.items(), key=lambda kv: -(kv[1] * (len(kv[0]) - 1)))
    pool = [a for a, c in scored[:top_k_candidates]]
    return sorted(pool, key=lambda a: (-len(a), -candidates[a]))[:max_atoms]

def encode_with_dict(word, dict_sorted_by_len_desc):
    n = len(word); atoms = []; i = 0
    while i < n:
        matched = None
        for atom in dict_sorted_by_len_desc:
            L = len(atom)
            if i + L <= n and word[i:i+L] == atom:
                matched = atom; break
        if matched:
            atoms.append(matched); i += len(matched)
        else:
            atoms.append(word[i]); i += 1
    return atoms

def full_report(words, label, min_freq=6):
    H0, H1 = char_entropy(words)
    ttr = len(set(words))/len(words)
    avglen = sum(len(w) for w in words)/len(words)
    unique_words = list(set(words))
    dictionary = build_dictionary_fast(unique_words, max_atoms=25, candidate_min_freq=min_freq)
    dict_sorted = sorted(dictionary, key=len, reverse=True)
    total_atoms = sum(len(encode_with_dict(w, dict_sorted)) for w in unique_words)
    total_chars = sum(len(w) for w in unique_words)
    compress = total_chars/total_atoms if total_atoms else float('nan')
    print(f"{label:<30} n={len(words):<6} TTR={ttr:.3f}  H1={H1:.3f}  avglen={avglen:.2f}  compress={compress:.3f}x")
    return dict(ttr=ttr, h1=H1, avglen=avglen, compress=compress)

results = {}

with open('../compare/hebrew_genesis_sample.txt', encoding='utf-8') as f:
    results['Hebrew_Genesis'] = full_report(f.read().split(), 'Hebrew (Genesis, narrative)')

with open('../compare/hebrew_exodus_sample.txt', encoding='utf-8') as f:
    results['Hebrew_Exodus'] = full_report(f.read().split(), 'Hebrew (Exodus, narrative)')

with open('../compare/hebrew_psalms_sample.txt', encoding='utf-8') as f:
    results['Hebrew_Psalms'] = full_report(f.read().split(), 'Hebrew (Psalms, poetic)')

with open('../compare/arabic_quran_consonantal.txt', encoding='utf-8') as f:
    results['Arabic_Baqarah'] = full_report(f.read().split(), 'Arabic (Al-Baqarah, legal)', min_freq=4)

with open('../compare/arabic_yusuf_sample.txt', encoding='utf-8') as f:
    results['Arabic_Yusuf'] = full_report(f.read().split(), 'Arabic (Yusuf, narrative)', min_freq=3)

print(f"\n{'Reference points:':<30}")
print(f"{'Voynichese A':<30} {'':6} TTR=0.320  H1=2.728  avglen=3.92  compress=1.200x")
print(f"{'Voynichese B':<30} {'':6} TTR=0.340  H1=2.420  avglen=4.33  compress=1.230x")
print(f"{'Culpeper English':<30} {'':6} TTR=0.304  H1=3.465  avglen=4.37  compress=1.153x")
print(f"{'Carmina Burana Latin':<30} {'':6} TTR=0.684  H1=3.098  avglen=5.37  compress=1.130x")
