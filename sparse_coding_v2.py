import re, math
from collections import Counter

def parse_fsg(path):
    records = []
    cur_lang = None; cur_section = None; cur_folio = None; cur_words = []
    def flush():
        if cur_words and cur_folio:
            records.append({'folio': cur_folio, 'lang': cur_lang, 'section': cur_section, 'words': list(cur_words)})
    with open(path, encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    for raw in lines:
        line = raw.rstrip('\n'); stripped = line.strip()
        if stripped.startswith('#'):
            comment = stripped.lstrip('#').strip(); low = comment.lower()
            if low.startswith('folio'):
                flush(); cur_words = []
                cur_folio = comment.split(None,1)[1].strip() if len(comment.split(None,1))>1 else comment
            if 'language a' in low: cur_lang='A'
            elif 'language b' in low: cur_lang='B'
            if 'herbal' in low: cur_section='herbal'
            elif 'biological' in low: cur_section='biological'
            elif 'pharma' in low or 'phamaceutical' in low: cur_section='pharmaceutical'
            elif 'star' in low: cur_section='stars'
            elif 'cosmological' in low: cur_section='cosmological'
            elif 'astronom' in low: cur_section='astronomical'
            continue
        if not stripped: continue
        text = re.sub(r'\{[^}]*\}', '', stripped)
        text = text.rstrip('-=')
        text = re.sub(r'\(([^|)]*)\|[^)]*\)', r'\1', text)
        for w in text.split(','):
            w = w.strip()
            if w: cur_words.append(w)
    flush()
    return records

recs = parse_fsg('raw_fsg.txt')
words_A, words_B = [], []
for r in recs:
    if r['lang'] == 'A': words_A.extend(r['words'])
    elif r['lang'] == 'B': words_B.extend(r['words'])

def encode_with_dict(word, dict_set_sorted_by_len_desc):
    """Greedy longest-match encoding. Returns list of atoms used."""
    n = len(word)
    atoms = []
    i = 0
    while i < n:
        matched = None
        for atom in dict_set_sorted_by_len_desc:
            L = len(atom)
            if L <= 1:
                continue
            if i + L <= n and word[i:i+L] == atom:
                matched = atom
                break
        if matched:
            atoms.append(matched)
            i += len(matched)
        else:
            atoms.append(word[i])  # fallback: single char "atom"
            i += 1
    return atoms

def total_atoms_needed(words, dict_set_sorted_by_len_desc):
    return sum(len(encode_with_dict(w, dict_set_sorted_by_len_desc)) for w in words)

def build_dictionary_v2(words, max_atoms=40, min_atom_len=2, max_atom_len=5, candidate_min_freq=4):
    """TRUE matching-pursuit-style dictionary learning:
    At each step, try EVERY candidate multi-char substring (length>=2) as a
    new dictionary atom, measure how much it REDUCES the total atoms-needed
    across the corpus (the real sparsity objective), and keep the single best
    one. Repeat. This directly optimizes sparsity instead of raw coverage,
    fixing v1's bias toward short/ubiquitous atoms."""
    # candidate pool: substrings of length 2..max_atom_len with min frequency
    candidates = Counter()
    for w in words:
        n = len(w)
        for L in range(min_atom_len, max_atom_len+1):
            for i in range(n - L + 1):
                candidates[w[i:i+L]] += 1
    candidates = {a for a, c in candidates.items() if c >= candidate_min_freq}
    print(f"    ({len(candidates)} candidate multi-char atoms with freq>={candidate_min_freq})")

    dictionary = []
    current_dict_sorted = []  # sorted by len desc for greedy matching
    baseline_atoms = total_atoms_needed(words, current_dict_sorted)
    print(f"    baseline atoms-needed (chars only): {baseline_atoms}")

    # Use a SAMPLE of words for the expensive search loop if corpus is large (speed),
    # but evaluate final dictionary on the FULL corpus
    sample_words = words if len(words) <= 2000 else words[:2000]

    for step in range(max_atoms):
        best_atom = None
        best_reduction = 0
        baseline = total_atoms_needed(sample_words, current_dict_sorted)
        for atom in list(candidates):
            trial_dict = sorted(current_dict_sorted + [atom], key=len, reverse=True)
            trial_total = total_atoms_needed(sample_words, trial_dict)
            reduction = baseline - trial_total
            if reduction > best_reduction:
                best_reduction = reduction
                best_atom = atom
        if best_atom is None or best_reduction <= 0:
            break
        dictionary.append(best_atom)
        candidates.discard(best_atom)
        current_dict_sorted = sorted(current_dict_sorted + [best_atom], key=len, reverse=True)

    return dictionary

print("=== SPARSE DICTIONARY LEARNING v2 (true sparsity-reduction objective) ===")
for label, words in [('A', words_A), ('B', words_B)]:
    print(f"\nLanguage {label}: {len(words)} words, {len(set(words))} unique")
    unique_words = list(set(words))
    dictionary = build_dictionary_v2(unique_words, max_atoms=30)
    print(f"  Learned dictionary ({len(dictionary)} atoms): {dictionary}")

    dict_sorted = sorted(dictionary, key=len, reverse=True)
    total_atoms = total_atoms_needed(unique_words, dict_sorted)
    total_chars = sum(len(w) for w in unique_words)
    avg_sparsity = total_atoms/len(unique_words)
    avg_len = total_chars/len(unique_words)
    print(f"  Avg atoms-per-word: {avg_sparsity:.2f}  (avg word length: {avg_len:.2f} chars)")
    print(f"  Compression ratio (chars per atom): {avg_len/avg_sparsity:.2f}")
