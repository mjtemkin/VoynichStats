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

# ---- SYLLABLE-LEVEL MODEL ----
# Voynichese is widely analyzed (Stolfi) as having PREFIX + MIDFIX + SUFFIX structure.
# Approximate this: split each real word into a prefix (up to first vowel-like char run),
# a middle, and a suffix (trailing consonant-like cluster), using EVA-ish heuristics
# adapted to this Currier-alphabet transliteration. Since we don't have a true
# phonological model, instead we'll do something more robust and well-established:
# extract all real 2-letter and 3-letter SUBSTRINGS used word-initially, word-finally,
# and medially, with frequency, and recombine THREE chosen chunks (init-chunk + mid-chunk
# + final-chunk) sampled with replacement from the REAL observed vocabulary's positional
# n-grams. This is a "word-template" or "slot" model rather than single chars.

def build_slot_model(words, k=2):
    """Build position-aware chunk inventories of length k from real words."""
    initials = Counter()
    finals = Counter()
    middles = Counter()
    lengths = Counter(len(w) for w in words)
    for w in words:
        if len(w) < 2*k:
            initials[w] += 1  # whole short word as its own "initial" chunk
            continue
        initials[w[:k]] += 1
        finals[w[-k:]] += 1
        if len(w) > 2*k:
            middles[w[k:-k]] += 1
        else:
            middles[''] += 1
    return initials, middles, finals, lengths

def generate_slot_corpus(words_real, n_words, k=2, seed=42):
    rng = random.Random(seed)
    initials, middles, finals, lengths = build_slot_model(words_real, k=k)
    init_pop, init_w = list(initials.keys()), list(initials.values())
    mid_pop, mid_w = list(middles.keys()), list(middles.values())
    fin_pop, fin_w = list(finals.keys()), list(finals.values())
    out = []
    for _ in range(n_words):
        ini = rng.choices(init_pop, weights=init_w)[0]
        mid = rng.choices(mid_pop, weights=mid_w)[0]
        fin = rng.choices(fin_pop, weights=fin_w)[0]
        word = ini + mid + fin
        out.append(word)
    return out

print("=== REAL vs SYLLABLE/SLOT-LEVEL GENERATED MODEL (k=2 chunk size) ===")
for label, real_words in [('A', words_A), ('B', words_B)]:
    synth = generate_slot_corpus(real_words, len(real_words), k=2, seed=42)
    real_s = full_stats(real_words)
    synth_s = full_stats(synth)
    print(f"\nLanguage {label}:")
    print(f"  REAL : n={real_s['n']:5d} H0={real_s['H0']:.3f} H1={real_s['H1']:.3f} TTR={real_s['ttr']:.3f} avglen={real_s['avglen']:.2f}")
    print(f"  SLOT : n={synth_s['n']:5d} H0={synth_s['H0']:.3f} H1={synth_s['H1']:.3f} TTR={synth_s['ttr']:.3f} avglen={synth_s['avglen']:.2f}")
    print(f"  Sample synthetic words: {synth[:12]}")

print("\n=== REAL vs SYLLABLE/SLOT-LEVEL GENERATED MODEL (k=3 chunk size) ===")
for label, real_words in [('A', words_A), ('B', words_B)]:
    synth = generate_slot_corpus(real_words, len(real_words), k=3, seed=42)
    real_s = full_stats(real_words)
    synth_s = full_stats(synth)
    print(f"\nLanguage {label}:")
    print(f"  REAL : n={real_s['n']:5d} H0={real_s['H0']:.3f} H1={real_s['H1']:.3f} TTR={real_s['ttr']:.3f} avglen={real_s['avglen']:.2f}")
    print(f"  SLOT : n={synth_s['n']:5d} H0={synth_s['H0']:.3f} H1={synth_s['H1']:.3f} TTR={synth_s['ttr']:.3f} avglen={synth_s['avglen']:.2f}")
    print(f"  Sample synthetic words: {synth[:12]}")
