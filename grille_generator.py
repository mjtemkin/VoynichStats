import re, math, random
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

def doubling_rate_flat(words):
    pairs = len(words)-1
    reps = sum(1 for i in range(pairs) if words[i]==words[i+1])
    return reps/pairs if pairs else 0

# ---- Build a REAL prefix/stem/suffix TABLE from real Voynichese words ----
# Using Stolfi-style decomposition heuristic: split each word into a short
# prefix (1-2 chars), a middle stem, and a short suffix (1-2 chars), based on
# real observed word-initial and word-final substrings and their frequencies.
def build_table(words, prefix_len=2, suffix_len=2):
    prefixes = Counter()
    stems = Counter()
    suffixes = Counter()
    for w in words:
        if len(w) <= prefix_len + suffix_len:
            # short word: treat whole thing as belonging mostly to "stem" with empty pre/suf
            stems[w] += 1
            prefixes[''] += 1
            suffixes[''] += 1
        else:
            prefixes[w[:prefix_len]] += 1
            stems[w[prefix_len:-suffix_len]] += 1
            suffixes[w[-suffix_len:]] += 1
    return prefixes, stems, suffixes

def grille_generate(words_real, n_words, prefix_len=2, suffix_len=2, blank_prob=0.05, seed=42):
    """Simulate the table-and-grille method:
    - build 3 columns (prefix, stem, suffix) from REAL syllable frequencies
    - 'slide the grille': maintain a moving pointer into each column's frequency-sorted
      list, advancing by a small random step each time (simulates physical sliding,
      which creates LOCAL correlation between consecutive words via overlapping picks)
    - some fraction of draws hit a 'blank' cell (empty syllable) per Rugg's own notes
    """
    rng = random.Random(seed)
    prefixes, stems, suffixes = build_table(words_real, prefix_len, suffix_len)

    # represent each column as a frequency-sorted list (like a real table laid out by freq)
    pre_list = [p for p, c in prefixes.most_common() for _ in range(c)]
    stem_list = [s for s, c in stems.most_common() for _ in range(c)]
    suf_list = [s for s, c in suffixes.most_common() for _ in range(c)]

    # grille pointers -- start at random position, advance with small random jitter
    # (simulates sliding the physical grille a small distance each time, NOT a fresh
    # independent random pick -- this is the mechanically important difference from
    # our earlier "slot" model)
    pre_ptr = rng.randrange(len(pre_list))
    stem_ptr = rng.randrange(len(stem_list))
    suf_ptr = rng.randrange(len(suf_list))

    out = []
    for _ in range(n_words):
        # small jitter: move each pointer by a small random step (sliding the grille)
        pre_ptr = (pre_ptr + rng.randint(-3, 3)) % len(pre_list)
        stem_ptr = (stem_ptr + rng.randint(-3, 3)) % len(stem_list)
        suf_ptr = (suf_ptr + rng.randint(-3, 3)) % len(suf_list)

        pre = pre_list[pre_ptr] if rng.random() > blank_prob else ''
        stem = stem_list[stem_ptr] if rng.random() > blank_prob else ''
        suf = suf_list[suf_ptr] if rng.random() > blank_prob else ''

        word = pre + stem + suf
        if word:  # skip fully-blank words
            out.append(word)
    return out

print("=== GRILLE/TABLE GENERATOR (sliding-pointer mechanism) vs REAL DATA ===")
for label, real_words in [('A', words_A), ('B', words_B)]:
    real_stats = full_stats(real_words)
    real_doubling = doubling_rate_flat(real_words)

    synth = grille_generate(real_words, len(real_words), seed=42)
    synth_stats = full_stats(synth)
    synth_doubling = doubling_rate_flat(synth)

    print(f"\nLanguage {label}:")
    print(f"  REAL : n={real_stats['n']:5d} TTR={real_stats['ttr']:.3f} H0={real_stats['H0']:.3f} "
          f"H1={real_stats['H1']:.3f} avglen={real_stats['avglen']:.2f} doubling={real_doubling*100:.3f}%")
    print(f"  GRILLE: n={synth_stats['n']:5d} TTR={synth_stats['ttr']:.3f} H0={synth_stats['H0']:.3f} "
          f"H1={synth_stats['H1']:.3f} avglen={synth_stats['avglen']:.2f} doubling={synth_doubling*100:.3f}%")
    print(f"  Sample generated words: {synth[:15]}")
