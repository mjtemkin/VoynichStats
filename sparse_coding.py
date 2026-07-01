import re, math, random
from collections import Counter, defaultdict

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

# ===== SPARSE CODING / DICTIONARY LEARNING (matching-pursuit style) =====
# Each word is "reconstructed" by greedily picking the longest/most-useful
# substring "atoms" that, concatenated, cover the word. This is a simplified
# matching-pursuit: atoms are candidate substrings, dictionary is built by
# keeping atoms that get reused most efficiently (cover the most total
# characters across the corpus per atom used), pruning rarely-used ones.

def generate_candidate_atoms(words, min_len=1, max_len=4):
    """All observed substrings of given lengths, with position tags (start/mid/end)."""
    atom_counts = Counter()
    for w in words:
        n = len(w)
        for L in range(min_len, max_len+1):
            for i in range(n - L + 1):
                atom_counts[w[i:i+L]] += 1
    return atom_counts

def build_dictionary(words, n_atoms=60, min_len=1, max_len=4):
    """Build a sparse dictionary via greedy coverage maximization (a simplified
    matching-pursuit dictionary learning loop):
    1. Start with all candidate substrings as atoms.
    2. Greedily pick the atom that covers the most yet-uncovered characters
       across the corpus, "use" it (mark covered), repeat until n_atoms chosen
       or coverage plateaus.
    This is the discrete-text analogue of sparse dictionary learning: atoms
    are reused as building blocks, and we want the SMALLEST dictionary that
    explains the MOST data (sparsity = few atoms needed per word)."""
    atom_counts = generate_candidate_atoms(words, min_len, max_len)
    # Only consider atoms that appear reasonably often (filters pure noise)
    candidates = {a: c for a, c in atom_counts.items() if c >= 3}

    dictionary = []
    remaining_words = [list(w) for w in words]  # mutable char lists, None = covered
    covered_chars = [[False]*len(w) for w in words]

    for _ in range(n_atoms):
        best_atom = None
        best_score = 0
        # score each candidate by how many currently-uncovered char positions it could cover
        atom_gain = Counter()
        for wi, w in enumerate(words):
            n = len(w)
            for L in range(min_len, max_len+1):
                for i in range(n - L + 1):
                    if all(not covered_chars[wi][i+k] for k in range(L)):
                        atom = w[i:i+L]
                        if atom in candidates:
                            atom_gain[atom] += L
        if not atom_gain:
            break
        best_atom, best_score = atom_gain.most_common(1)[0]
        if best_score < 5:
            break
        dictionary.append(best_atom)
        # mark covered (greedily, leftmost-first non-overlapping occurrences)
        for wi, w in enumerate(words):
            n = len(w); L = len(best_atom)
            i = 0
            while i <= n - L:
                if w[i:i+L] == best_atom and all(not covered_chars[wi][i+k] for k in range(L)):
                    for k in range(L):
                        covered_chars[wi][i+k] = True
                    i += L
                else:
                    i += 1
    return dictionary

def encode_word_sparsity(word, dictionary):
    """Greedily encode a word using dictionary atoms (longest-match first),
    return (num_atoms_used, coverage_fraction)."""
    sorted_dict = sorted(set(dictionary), key=len, reverse=True)
    n = len(word)
    covered = [False]*n
    atoms_used = 0
    i = 0
    while i < n:
        matched = False
        for atom in sorted_dict:
            L = len(atom)
            if i + L <= n and word[i:i+L] == atom:
                atoms_used += 1
                i += L
                matched = True
                break
        if not matched:
            i += 1  # uncovered character, move on (counts as a "miss")
            atoms_used += 1  # treat as a trivial 1-char atom
    return atoms_used

print("=== BUILDING SPARSE DICTIONARIES (matching-pursuit style) ===")
for label, words in [('A', words_A), ('B', words_B)]:
    print(f"\nLanguage {label}: {len(words)} words, {len(set(words))} unique")
    dictionary = build_dictionary(words, n_atoms=50)
    print(f"  Learned dictionary ({len(dictionary)} atoms): {dictionary}")

    # Average sparsity: how many atoms needed per word, on average?
    sparsities = [encode_word_sparsity(w, dictionary) for w in set(words)]
    avg_sparsity = sum(sparsities)/len(sparsities)
    avg_word_len = sum(len(w) for w in set(words))/len(set(words))
    print(f"  Avg atoms-per-word (sparsity): {avg_sparsity:.2f}  (avg word length: {avg_word_len:.2f} chars)")
    print(f"  Compression ratio (chars per atom): {avg_word_len/avg_sparsity:.2f}")
