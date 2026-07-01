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

def build_table(words, prefix_len=2, suffix_len=2):
    prefixes = Counter(); stems = Counter(); suffixes = Counter()
    for w in words:
        if len(w) <= prefix_len + suffix_len:
            stems[w] += 1; prefixes[''] += 1; suffixes[''] += 1
        else:
            prefixes[w[:prefix_len]] += 1
            stems[w[prefix_len:-suffix_len]] += 1
            suffixes[w[-suffix_len:]] += 1
    return prefixes, stems, suffixes

def grille_generate_v2(words_real, n_words, prefix_len=2, suffix_len=2, blank_prob=0.05,
                        jitter=2, seed=42):
    """FIXED VERSION: each column is a list of ONE ENTRY PER DISTINCT SYLLABLE
    (table physically laid out with distinct cells), ordered by descending frequency
    (so the table itself isn't random, matching Rugg's description of a structured
    table). Selection probability still respects frequency via WEIGHTED sliding:
    instead of a uniform random walk over distinct-cell positions, the grille slides
    a small step but the WIDTH each cell occupies on the table is proportional to
    its frequency -- i.e. a continuous position variable, mapped through the
    cumulative frequency distribution. This is a more faithful mechanical analogue:
    a physical table would naturally devote more *space* to common syllables if a
    hoaxer wrote frequent ones in multiple cells, while the grille's MOVEMENT
    through physical space is what's locally correlated (sliding a few cells),
    not the selection of distinct items.
    """
    rng = random.Random(seed)
    prefixes, stems, suffixes = build_table(words_real, prefix_len, suffix_len)

    def make_cumulative(counter):
        items = list(counter.items())
        total = sum(c for _, c in items)
        cum = []
        running = 0
        for item, c in items:
            running += c
            cum.append((running/total, item))
        return cum

    pre_cum = make_cumulative(prefixes)
    stem_cum = make_cumulative(stems)
    suf_cum = make_cumulative(suffixes)

    def lookup(cum, pos):
        # pos in [0,1) -- find first entry with cumulative >= pos
        for threshold, item in cum:
            if pos <= threshold:
                return item
        return cum[-1][1]

    # grille position is a continuous [0,1) value per column, sliding by small steps
    pre_pos = rng.random(); stem_pos = rng.random(); suf_pos = rng.random()
    step_size = jitter / 100.0  # small slide per word

    out = []
    for _ in range(n_words):
        pre_pos = (pre_pos + rng.uniform(-step_size, step_size)) % 1.0
        stem_pos = (stem_pos + rng.uniform(-step_size, step_size)) % 1.0
        suf_pos = (suf_pos + rng.uniform(-step_size, step_size)) % 1.0

        pre = lookup(pre_cum, pre_pos) if rng.random() > blank_prob else ''
        stem = lookup(stem_cum, stem_pos) if rng.random() > blank_prob else ''
        suf = lookup(suf_cum, suf_pos) if rng.random() > blank_prob else ''

        word = pre + stem + suf
        if word:
            out.append(word)
    return out

print("=== GRILLE GENERATOR v2 (continuous sliding position, frequency-weighted lookup) ===")
for label, real_words in [('A', words_A), ('B', words_B)]:
    real_stats = full_stats(real_words)
    real_doubling = doubling_rate_flat(real_words)

    best_result = None
    for step in [0.5, 1, 2, 4, 8, 15]:
        synth = grille_generate_v2(real_words, len(real_words), jitter=step, seed=42)
        if len(synth) < 10:
            continue
        synth_stats = full_stats(synth)
        synth_doubling = doubling_rate_flat(synth)
        diff = abs(synth_doubling - real_doubling) + abs(synth_stats['ttr'] - real_stats['ttr'])
        if best_result is None or diff < best_result[0]:
            best_result = (diff, step, synth_stats, synth_doubling, synth)

    diff, step, synth_stats, synth_doubling, synth = best_result
    print(f"\nLanguage {label}: (best jitter step={step})")
    print(f"  REAL  : n={real_stats['n']:5d} TTR={real_stats['ttr']:.3f} H0={real_stats['H0']:.3f} "
          f"H1={real_stats['H1']:.3f} avglen={real_stats['avglen']:.2f} doubling={real_doubling*100:.3f}%")
    print(f"  GRILLE: n={synth_stats['n']:5d} TTR={synth_stats['ttr']:.3f} H0={synth_stats['H0']:.3f} "
          f"H1={synth_stats['H1']:.3f} avglen={synth_stats['avglen']:.2f} doubling={synth_doubling*100:.3f}%")
    print(f"  Sample: {synth[:15]}")
