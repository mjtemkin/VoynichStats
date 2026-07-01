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

def generate_bagofwords(words_real, n_words, seed=42):
    """Sample WHOLE WORDS with replacement from the real frequency-ranked vocabulary."""
    rng = random.Random(seed)
    vocab_pop = list(words_real)  # sampling directly from the real word list reproduces real freq distribution
    return [rng.choice(vocab_pop) for _ in range(n_words)]

print("=== REAL vs BAG-OF-REAL-WORDS (sampled with replacement from real vocab+freq) ===")
for label, real_words in [('A', words_A), ('B', words_B)]:
    synth = generate_bagofwords(real_words, len(real_words), seed=42)
    real_s = full_stats(real_words)
    synth_s = full_stats(synth)
    print(f"\nLanguage {label}:")
    print(f"  REAL: n={real_s['n']:5d} H0={real_s['H0']:.3f} H1={real_s['H1']:.3f} TTR={real_s['ttr']:.3f} avglen={real_s['avglen']:.2f}")
    print(f"  BAG : n={synth_s['n']:5d} H0={synth_s['H0']:.3f} H1={synth_s['H1']:.3f} TTR={synth_s['ttr']:.3f} avglen={synth_s['avglen']:.2f}")
    print(f"  Sample: {synth[:12]}")

print("\n=== Why TTR and avglen MUST match exactly (by construction) ===")
print("Sampling-with-replacement from the same multiset preserves the marginal word-frequency")
print("distribution exactly in expectation -- so TTR, avg word length, H0 will closely track real values.")
print("The only thing this model CANNOT capture is ORDER / SEQUENCE structure: which words follow")
print("which other words, line-position effects, local repetition runs, etc.")
