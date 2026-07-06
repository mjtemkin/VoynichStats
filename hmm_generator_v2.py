"""
Level 4.5 generator: HMM with word-class ordering + stickiness + temperature sampling.

New addition: temperature parameter alpha that controls vocabulary diversity.
- alpha=1.0: original empirical frequency distribution (what we had before)
- alpha<1.0: flatter distribution, more rare words sampled (increases TTR)
- alpha>1.0: more concentrated (decreases TTR)

Free parameters: p_stick (doubling) and alpha (TTR). Both calibrated jointly.
"""
import re, math, random
from collections import Counter, defaultdict

def parse_fsg_with_lines(path):
    records = []
    cur_lang = None; cur_section = None; cur_folio = None
    cur_lines = []; cur_line_words = []
    def flush_line():
        nonlocal cur_line_words
        if cur_line_words:
            cur_lines.append(cur_line_words[:])
            cur_line_words = []
    def flush_folio():
        flush_line()
        if cur_lines and cur_folio:
            records.append({'folio': cur_folio, 'lang': cur_lang,
                          'section': cur_section, 'lines': [l[:] for l in cur_lines]})
        cur_lines.clear()
    with open(path, encoding='utf-8', errors='replace') as f:
        raw_lines = f.readlines()
    for raw in raw_lines:
        line = raw.rstrip('\n'); stripped = line.strip()
        if stripped.startswith('#'):
            comment = stripped.lstrip('#').strip(); low = comment.lower()
            if low.startswith('folio'):
                flush_folio()
                cur_folio = comment.split(None,1)[1].strip() if len(comment.split(None,1))>1 else comment
            if 'language a' in low or "currier's language a" in low: cur_lang='A'
            elif 'language b' in low or "currier's language b" in low: cur_lang='B'
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
        words_here = [w.strip() for w in text.split(',') if w.strip()]
        if words_here:
            cur_line_words.extend(words_here)
        flush_line()
    flush_folio()
    return records

recs = parse_fsg_with_lines('raw_fsg.txt')
lines_A, lines_B = [], []
for r in recs:
    if r['lang']=='A': lines_A.extend(r['lines'])
    elif r['lang']=='B': lines_B.extend(r['lines'])

def classify_word(w, suffix_len=2):
    return w[-suffix_len:] if len(w) >= suffix_len else w

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

def doubling_rate(lines):
    pairs = reps = 0
    for line in lines:
        for i in range(len(line)-1):
            pairs += 1
            if line[i]==line[i+1]: reps += 1
    return reps/pairs if pairs else 0

def word_class_asym(lines, n_classes=10, max_ratio=3.0, min_total=10):
    class_counts = Counter(classify_word(w) for l in lines for w in l)
    top_classes = [c for c,_ in class_counts.most_common(n_classes)]
    class_set = set(top_classes)
    pair_counts = Counter()
    for line in lines:
        tags = [classify_word(w) for w in line]
        for i in range(len(tags)-1):
            a,b = tags[i], tags[i+1]
            if a in class_set and b in class_set:
                pair_counts[(a,b)] += 1
    results = []
    for i,x in enumerate(top_classes):
        for y in top_classes[i+1:]:
            fx,fy = class_counts[x], class_counts[y]
            if min(fx,fy)==0 or max(fx,fy)/min(fx,fy)>max_ratio: continue
            xy = pair_counts.get((x,y),0); yx = pair_counts.get((y,x),0)
            total = xy+yx
            if total >= min_total:
                results.append(abs((xy-yx)/total))
    return sum(results)/len(results) if results else 0

def full_stats(lines):
    words = [w for l in lines for w in l]
    H0, H1 = char_entropy(words)
    ttr = len(set(words))/len(words)
    avglen = sum(len(w) for w in words)/len(words)
    dr = doubling_rate(lines)
    asym = word_class_asym(lines)
    return dict(n=len(words), H1=H1, ttr=ttr, avglen=avglen,
                doubling=dr, asym=asym)

def learn_transition_matrix(lines, n_classes=15):
    class_counts = Counter(classify_word(w) for l in lines for w in l)
    top_classes = [c for c,_ in class_counts.most_common(n_classes)]
    class_set = set(top_classes)
    trans = defaultdict(Counter)
    for line in lines:
        tags = [classify_word(w) for w in line]
        for i in range(len(tags)-1):
            a,b = tags[i], tags[i+1]
            if a in class_set and b in class_set:
                trans[a][b] += 1
    trans_prob = {}
    for src in top_classes:
        total = sum(trans[src].values())
        if total > 0:
            trans_prob[src] = {dst: cnt/total for dst,cnt in trans[src].items()}
        else:
            trans_prob[src] = {c: 1/len(top_classes) for c in top_classes}
    return top_classes, trans_prob

def build_temperature_vocab(lines, top_classes, alpha=1.0):
    """Build per-class vocabulary with temperature-adjusted sampling weights."""
    class_vocab = defaultdict(Counter)
    all_words_counter = Counter()
    for line in lines:
        for w in line:
            cls = classify_word(w)
            class_vocab[cls][w] += 1
            all_words_counter[w] += 1

    # Apply temperature: weight = count^alpha
    class_vocab_weighted = {}
    for cls in top_classes:
        if class_vocab[cls]:
            words = list(class_vocab[cls].keys())
            weights = [class_vocab[cls][w]**alpha for w in words]
            class_vocab_weighted[cls] = (words, weights)

    # Fallback pool (all words, temperature adjusted)
    all_words = list(all_words_counter.keys())
    all_weights = [all_words_counter[w]**alpha for w in all_words]
    return class_vocab_weighted, all_words, all_weights

def generate_v2(lines_real, p_stick, alpha=1.0, n_classes=15, seed=42):
    rng = random.Random(seed)
    top_classes, trans_prob = learn_transition_matrix(lines_real, n_classes)
    class_vocab, all_words, all_weights = build_temperature_vocab(
        lines_real, top_classes, alpha=alpha)
    line_lens = [len(l) for l in lines_real]

    out_lines = []
    prev_word = None
    cur_class = rng.choice(top_classes)

    for ln in line_lens:
        line_out = []
        for i in range(ln):
            if prev_word is not None and rng.random() < p_stick:
                word = prev_word
            else:
                # Sample next class from transition distribution
                if prev_word is not None and cur_class in trans_prob:
                    next_classes = list(trans_prob[cur_class].keys())
                    next_probs = [trans_prob[cur_class][c] for c in next_classes]
                    cur_class = rng.choices(next_classes, weights=next_probs)[0]
                else:
                    cur_class = rng.choice(top_classes)
                # Sample word from class vocabulary with temperature
                if cur_class in class_vocab:
                    words, weights = class_vocab[cur_class]
                    word = rng.choices(words, weights=weights)[0]
                else:
                    word = rng.choices(all_words, weights=all_weights)[0]
            line_out.append(word)
            prev_word = word
            cur_class = classify_word(word)
        out_lines.append(line_out)
    return out_lines

def fit_score(real, synth):
    """Composite fit: sum of squared normalized deviations across 5 metrics."""
    metrics = ['H1', 'ttr', 'avglen', 'doubling', 'asym']
    score = 0
    for m in metrics:
        r = real[m]; s = synth[m]
        if r > 0:
            score += ((s - r) / r) ** 2
    return score

print("=== LEVEL 4.5 GENERATOR: HMM + stickiness + temperature sampling ===\n")
print("Searching over (p_stick, alpha) grid to minimize composite fit score...\n")

p_stick_vals = [0.0, 0.002, 0.004, 0.006, 0.008]
alpha_vals   = [0.3, 0.5, 0.7, 0.9, 1.0, 1.2]

for label, lines in [('A', lines_A), ('B', lines_B)]:
    real_s = full_stats(lines)
    print(f"Language {label} REAL: H1={real_s['H1']:.3f} TTR={real_s['ttr']:.3f} "
          f"avglen={real_s['avglen']:.2f} doubling={real_s['doubling']*100:.3f}% "
          f"asym={real_s['asym']:.3f}")

    best = None
    for p in p_stick_vals:
        for alpha in alpha_vals:
            synth_lines = generate_v2(lines, p_stick=p, alpha=alpha, seed=42)
            synth_s = full_stats(synth_lines)
            score = fit_score(real_s, synth_s)
            if best is None or score < best[0]:
                best = (score, p, alpha, synth_s)

    score, p, alpha, synth_s = best
    print(f"\nBEST: p_stick={p}, alpha={alpha} (fit score={score:.4f})")
    print(f"  H1   : real={real_s['H1']:.3f}  synth={synth_s['H1']:.3f}  "
          f"err={abs(synth_s['H1']-real_s['H1'])/real_s['H1']*100:.1f}%")
    print(f"  TTR  : real={real_s['ttr']:.3f}  synth={synth_s['ttr']:.3f}  "
          f"err={abs(synth_s['ttr']-real_s['ttr'])/real_s['ttr']*100:.1f}%")
    print(f"  avglen: real={real_s['avglen']:.2f}  synth={synth_s['avglen']:.2f}  "
          f"err={abs(synth_s['avglen']-real_s['avglen'])/real_s['avglen']*100:.1f}%")
    print(f"  doubl: real={real_s['doubling']*100:.3f}%  synth={synth_s['doubling']*100:.3f}%  "
          f"err={abs(synth_s['doubling']-real_s['doubling'])/max(real_s['doubling'],1e-6)*100:.1f}%")
    print(f"  asym : real={real_s['asym']:.3f}  synth={synth_s['asym']:.3f}  "
          f"err={abs(synth_s['asym']-real_s['asym'])/real_s['asym']*100:.1f}%")
    print()
