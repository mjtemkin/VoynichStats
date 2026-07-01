import re, math, random
from collections import Counter, defaultdict

def parse_fsg(path):
    records = []
    cur_lang = None
    cur_section = None
    cur_folio = None
    cur_words = []
    def flush():
        if cur_words and cur_folio:
            records.append({'folio': cur_folio, 'lang': cur_lang, 'section': cur_section, 'words': list(cur_words)})
    with open(path, encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    for raw in lines:
        line = raw.rstrip('\n')
        stripped = line.strip()
        if stripped.startswith('#'):
            comment = stripped.lstrip('#').strip()
            low = comment.lower()
            if low.startswith('folio'):
                flush()
                cur_words = []
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
words_A = []
words_B = []
for r in recs:
    if r['lang'] == 'A':
        words_A.extend(r['words'])
    elif r['lang'] == 'B':
        words_B.extend(r['words'])

print(f"Real A: {len(words_A)} words. Real B: {len(words_B)} words.")

# ---- measurement functions (same as before) ----
def char_entropy(words):
    corpus = ''.join(words)
    counts = Counter(corpus)
    total = sum(counts.values())
    H0 = -sum((c/total)*math.log2(c/total) for c in counts.values())
    bigrams = Counter(); ctx = Counter()
    for i in range(len(corpus)-1):
        a,b = corpus[i], corpus[i+1]
        bigrams[(a,b)] += 1
        ctx[a] += 1
    H1 = 0.0
    for (a,b),cnt in bigrams.items():
        p_ab = cnt/total
        p_b_given_a = cnt/ctx[a]
        H1 -= p_ab * math.log2(p_b_given_a)
    return H0, H1

def full_stats(words):
    H0, H1 = char_entropy(words)
    ttr = len(set(words))/len(words)
    avglen = sum(len(w) for w in words)/len(words)
    return dict(n=len(words), H0=H0, H1=H1, ttr=ttr, avglen=avglen)

# ---- Train an order-1 (bigram) Markov model on REAL word-length distribution + char transitions ----
def train_markov(words):
    """Build: start-char distribution, transition table P(next|current), word-length distribution"""
    starts = Counter(w[0] for w in words if w)
    trans = defaultdict(Counter)
    for w in words:
        for i in range(len(w)-1):
            trans[w[i]][w[i+1]] += 1
    lengths = Counter(len(w) for w in words)
    return starts, trans, lengths

def generate_word(starts, trans, length, rng):
    chars_pop = list(starts.keys())
    chars_w = list(starts.values())
    w = [rng.choices(chars_pop, weights=chars_w)[0]]
    for _ in range(length-1):
        cur = w[-1]
        if cur in trans and trans[cur]:
            nxt_pop = list(trans[cur].keys())
            nxt_w = list(trans[cur].values())
            w.append(rng.choices(nxt_pop, weights=nxt_w)[0])
        else:
            # fallback: pick from global start distribution
            w.append(rng.choices(chars_pop, weights=chars_w)[0])
    return ''.join(w)

def generate_corpus(words_real, n_words, seed=42):
    rng = random.Random(seed)
    starts, trans, lengths = train_markov(words_real)
    len_pop = list(lengths.keys())
    len_w = list(lengths.values())
    out = []
    for _ in range(n_words):
        L = rng.choices(len_pop, weights=len_w)[0]
        L = max(L, 1)
        out.append(generate_word(starts, trans, L, rng))
    return out

print("\n=== REAL vs MARKOV-GENERATED (order-1 char model, real length distribution) ===")
for label, real_words in [('A', words_A), ('B', words_B)]:
    synth = generate_corpus(real_words, len(real_words), seed=42)
    real_s = full_stats(real_words)
    synth_s = full_stats(synth)
    print(f"\nLanguage {label}:")
    print(f"  REAL : n={real_s['n']:5d} H0={real_s['H0']:.3f} H1={real_s['H1']:.3f} TTR={real_s['ttr']:.3f} avglen={real_s['avglen']:.2f}")
    print(f"  MARKOV: n={synth_s['n']:5d} H0={synth_s['H0']:.3f} H1={synth_s['H1']:.3f} TTR={synth_s['ttr']:.3f} avglen={synth_s['avglen']:.2f}")
    print(f"  Sample synthetic words: {synth[:12]}")
