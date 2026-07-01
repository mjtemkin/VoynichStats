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

def build_dictionary_fast(words, max_atoms=25, min_atom_len=2, max_atom_len=5, candidate_min_freq=8, top_k_candidates=80):
    candidates = Counter()
    for w in words:
        n = len(w)
        for L in range(min_atom_len, max_atom_len+1):
            for i in range(n - L + 1):
                candidates[w[i:i+L]] += 1
    candidates = {a: c for a, c in candidates.items() if c >= candidate_min_freq}
    scored = sorted(candidates.items(), key=lambda kv: -(kv[1] * (len(kv[0]) - 1)))
    pool = [a for a, c in scored[:top_k_candidates]]
    pool_sorted = sorted(pool, key=lambda a: (-len(a), -candidates[a]))
    return pool_sorted[:max_atoms]

def encode_with_dict(word, dict_sorted_by_len_desc):
    n = len(word)
    atoms = []
    i = 0
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

with open('../compare/arabic_quran_consonantal.txt', encoding='utf-8') as f:
    text = f.read()
arabic_words = text.split()

print(f"Arabic (consonantal Quran): {len(arabic_words)} words, {len(set(arabic_words))} unique")

H0, H1 = char_entropy(arabic_words)
ttr = len(set(arabic_words))/len(arabic_words)
avglen = sum(len(w) for w in arabic_words)/len(arabic_words)
print(f"TTR={ttr:.3f}  H0={H0:.3f}  H1={H1:.3f}  avglen={avglen:.2f}")

unique_words = list(set(arabic_words))
dictionary = build_dictionary_fast(unique_words, max_atoms=25, candidate_min_freq=6)
dict_sorted = sorted(dictionary, key=len, reverse=True)
print(f"Learned dictionary: {dictionary}")

total_atoms = sum(len(encode_with_dict(w, dict_sorted)) for w in unique_words)
total_chars = sum(len(w) for w in unique_words)
compress = total_chars/total_atoms
print(f"Compression ratio: {compress:.3f}x")
print("Example encodings:")
for w in unique_words[:8]:
    print(f"  {w} -> {encode_with_dict(w, dict_sorted)}")
