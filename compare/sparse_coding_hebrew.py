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
    return dictionary, candidates

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
            atoms.append(matched)
            i += len(matched)
        else:
            atoms.append(word[i])
            i += 1
    return atoms

def run_on_corpus(words, label, max_atoms=25, candidate_min_freq=8):
    unique_words = list(set(words))
    print(f"\n{label}: {len(words)} words, {len(unique_words)} unique")
    dictionary, candidates = build_dictionary_fast(unique_words, max_atoms=max_atoms, candidate_min_freq=candidate_min_freq)
    dict_sorted = sorted(dictionary, key=len, reverse=True)
    print(f"  Learned dictionary ({len(dictionary)} atoms): {dictionary}")

    total_atoms = 0; total_chars = 0
    for w in unique_words:
        atoms = encode_with_dict(w, dict_sorted)
        total_atoms += len(atoms); total_chars += len(w)
    avg_sparsity = total_atoms/len(unique_words)
    avg_len = total_chars/len(unique_words)
    ratio = avg_len/avg_sparsity
    print(f"  Avg atoms-per-word: {avg_sparsity:.2f}  (avg word length: {avg_len:.2f} chars)")
    print(f"  Compression ratio (chars per atom): {ratio:.2f}")
    print(f"  Example encodings:")
    for w in unique_words[:8]:
        print(f"    {w} -> {encode_with_dict(w, dict_sorted)}")
    return ratio

with open('compare/hebrew_genesis_sample.txt', encoding='utf-8') as f:
    text = f.read()
# Hebrew words include maqaf (־) as a hyphen-like joiner; strip punctuation, keep Hebrew letters only
hebrew_words = re.findall(r"[\u05D0-\u05EA]+", text)

print("=== SPARSE DICTIONARY LEARNING ON REAL CONSONANTAL HEBREW (Genesis) ===")
ratio_hebrew = run_on_corpus(hebrew_words, "Genesis (real consonantal Hebrew)", max_atoms=25, candidate_min_freq=8)

print("\n=== UPDATED COMPARISON TABLE ===")
print(f"{'Corpus':<35}{'Compression ratio':>20}")
print(f"{'Genesis (real Hebrew, consonantal)':<35}{ratio_hebrew:>19.2f}x")
print(f"{'Culpeper (real English, n=2371)':<35}{1.13:>19.2f}x")
print(f"{'Carmina Burana (real Latin)':<35}{1.13:>19.2f}x")
print(f"{'Voynichese A':<35}{1.20:>19.2f}x")
print(f"{'Voynichese B':<35}{1.23:>19.2f}x")
