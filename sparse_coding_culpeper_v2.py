import re
from collections import Counter

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
    dictionary = pool_sorted[:max_atoms]
    return dictionary

def encode_with_dict(word, dict_sorted_by_len_desc):
    n = len(word)
    atoms = []
    i = 0
    while i < n:
        matched = None
        for atom in dict_sorted_by_len_desc:
            L = len(atom)
            if i + L <= n and word[i:i+L] == atom:
                matched = atom
                break
        if matched:
            atoms.append(matched); i += len(matched)
        else:
            atoms.append(word[i]); i += 1
    return atoms

def run_on_corpus(words, label, max_atoms=25, candidate_min_freq=4):
    unique_words = list(set(words))
    dictionary = build_dictionary_fast(unique_words, max_atoms=max_atoms, candidate_min_freq=candidate_min_freq)
    dict_sorted = sorted(dictionary, key=len, reverse=True)
    total_atoms = sum(len(encode_with_dict(w, dict_sorted)) for w in unique_words)
    total_chars = sum(len(w) for w in unique_words)
    ratio = total_chars/total_atoms
    print(f"{label}: {len(words)} words, {len(unique_words)} unique, ratio={ratio:.3f}x")
    return ratio

with open('../compare/culpeper_full.txt') as f:
    text = f.read()
words = re.findall(r"[a-z]+", text.lower())
print(f"Culpeper expanded sample: {len(words)} words total")
ratio = run_on_corpus(words, "Culpeper (expanded)")
