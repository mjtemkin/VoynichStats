import re
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

def build_dictionary_fast(words, max_atoms=25, min_atom_len=2, max_atom_len=5, candidate_min_freq=8, top_k_candidates=80):
    """Faster version: 
    1. Restrict candidate pool to just the TOP-K most frequent substrings (by raw count),
       which is a much smaller, cheap-to-search set than 'all candidates above min freq'.
    2. Score each candidate's REDUCTION via a cheap approximation: gain = (freq * (len-1)),
       i.e. "how many extra characters would this atom let us skip per occurrence" --
       this is mathematically closer to the real sparsity objective than v1's raw coverage,
       because a length-3 atom used 50 times saves 2*50=100 atom-slots versus spelling it
       letter by letter, while a length-1 'atom' saves 0 by definition. This avoids the
       O(candidates x words) re-evaluation loop from v2 while fixing v1's actual bug
       (treating length-1 atoms as competitive).
    3. After picking top candidates this way once, do ONE proper greedy non-overlapping
       coverage pass per word for the FINAL evaluation only.
    """
    # Step 1: candidate pool (length >= 2 only -- this alone fixes v1's degenerate bug)
    candidates = Counter()
    for w in words:
        n = len(w)
        for L in range(min_atom_len, max_atom_len+1):
            for i in range(n - L + 1):
                candidates[w[i:i+L]] += 1
    candidates = {a: c for a, c in candidates.items() if c >= candidate_min_freq}

    # Step 2: score by approx sparsity gain = freq * (len - 1), take top_k as initial pool
    scored = sorted(candidates.items(), key=lambda kv: -(kv[1] * (len(kv[0]) - 1)))
    pool = [a for a, c in scored[:top_k_candidates]]

    # Step 3: greedily select non-redundant atoms from the pool by ACTUAL incremental
    # sparsity gain, evaluated on a capped sample for speed, but using a cheap formula:
    # an atom's marginal value = (its frequency among positions not yet covered by
    # already-chosen LONGER atoms) * (len-1). We approximate "not yet covered" by simply
    # processing atoms longest-first (longer atoms get first claim, consistent with how
    # greedy longest-match encoding will use them anyway).
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
            atoms.append(matched)
            i += len(matched)
        else:
            atoms.append(word[i])
            i += 1
    return atoms

print("=== SPARSE DICTIONARY LEARNING v3 (fast, frequency*length-gain objective) ===")
for label, words in [('A', words_A), ('B', words_B)]:
    unique_words = list(set(words))
    print(f"\nLanguage {label}: {len(words)} words, {len(unique_words)} unique")
    dictionary = build_dictionary_fast(unique_words, max_atoms=25)
    dict_sorted = sorted(dictionary, key=len, reverse=True)
    print(f"  Learned dictionary ({len(dictionary)} atoms): {dictionary}")

    total_atoms = 0
    total_chars = 0
    for w in unique_words:
        atoms = encode_with_dict(w, dict_sorted)
        total_atoms += len(atoms)
        total_chars += len(w)
    avg_sparsity = total_atoms/len(unique_words)
    avg_len = total_chars/len(unique_words)
    print(f"  Avg atoms-per-word: {avg_sparsity:.2f}  (avg word length: {avg_len:.2f} chars)")
    print(f"  Compression ratio (chars per atom): {avg_len/avg_sparsity:.2f}")

    # show a few example encodings
    print(f"  Example encodings:")
    for w in unique_words[:8]:
        print(f"    {w} -> {encode_with_dict(w, dict_sorted)}")
