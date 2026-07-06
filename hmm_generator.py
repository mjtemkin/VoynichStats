"""
Level 4 generator: sticky bag-of-words WITH word-class ordering structure.

Architecture:
- Words are drawn from the real vocabulary weighted by frequency
- The next word's suffix-class is sampled from a learned asymmetric
  transition matrix (reproducing the word-class ordering asymmetry)
- With probability p_stick, the previous word is repeated regardless
  of class (reproducing the doubling anomaly)

Free parameters: p_stick (calibrated to match real doubling rate)
The transition matrix is learned from data, not a free parameter.
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
    """Average |asymmetry| across frequency-matched class pairs."""
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
    return dict(n=len(words), H0=H0, H1=H1, ttr=ttr, avglen=avglen,
                doubling=dr, asym=asym)

# ===== LEARN CLASS TRANSITION MATRIX from real data =====
def learn_transition_matrix(lines, n_classes=15):
    class_counts = Counter(classify_word(w) for l in lines for w in l)
    top_classes = [c for c,_ in class_counts.most_common(n_classes)]
    class_set = set(top_classes)
    # count transitions between classes
    trans = defaultdict(Counter)
    for line in lines:
        tags = [classify_word(w) for w in line]
        for i in range(len(tags)-1):
            a,b = tags[i], tags[i+1]
            if a in class_set and b in class_set:
                trans[a][b] += 1
    # normalize to get P(next_class | current_class)
    trans_prob = {}
    for src in top_classes:
        total = sum(trans[src].values())
        if total > 0:
            trans_prob[src] = {dst: cnt/total for dst,cnt in trans[src].items()}
        else:
            # uniform fallback
            trans_prob[src] = {c: 1/len(top_classes) for c in top_classes}
    return top_classes, trans_prob

def build_class_vocabulary(lines, top_classes):
    """Build {class -> [words in that class with repetitions]}"""
    class_vocab = defaultdict(list)
    for line in lines:
        for w in line:
            cls = classify_word(w)
            if cls in set(top_classes):
                class_vocab[cls].append(w)
    # fallback pool for classes not in top_classes
    all_words = [w for l in lines for w in l]
    return class_vocab, all_words

def generate_hmm_corpus(lines_real, p_stick, n_classes=15, seed=42):
    """Generate a corpus using the Level 4 HMM generator."""
    rng = random.Random(seed)
    top_classes, trans_prob = learn_transition_matrix(lines_real, n_classes)
    class_vocab, all_words = build_class_vocabulary(lines_real, top_classes)
    line_lens = [len(l) for l in lines_real]

    out_lines = []
    prev_word = None
    cur_class = rng.choice(top_classes)  # start in a random class

    for ln in line_lens:
        line_out = []
        for i in range(ln):
            # Step 1: with p_stick, just repeat previous word
            if prev_word is not None and rng.random() < p_stick:
                word = prev_word
            else:
                # Step 2: sample next class from transition distribution
                if prev_word is not None and cur_class in trans_prob:
                    next_classes = list(trans_prob[cur_class].keys())
                    next_probs = [trans_prob[cur_class][c] for c in next_classes]
                    cur_class = rng.choices(next_classes, weights=next_probs)[0]
                else:
                    cur_class = rng.choice(top_classes)
                # Step 3: sample a word from that class's vocabulary
                if class_vocab[cur_class]:
                    word = rng.choice(class_vocab[cur_class])
                else:
                    word = rng.choice(all_words)  # fallback
            line_out.append(word)
            prev_word = word
            cur_class = classify_word(word)
        out_lines.append(line_out)
    return out_lines

# ===== FIT COMPOSITE SCORE =====
def fit_score(real_stats, synth_stats):
    """Lower is better. Sum of squared normalized deviations across 5 key metrics."""
    metrics = ['H1', 'ttr', 'avglen', 'doubling', 'asym']
    score = 0
    for m in metrics:
        r = real_stats[m.lower()] if m.lower() in real_stats else real_stats.get(m, 0)
        s = synth_stats[m.lower()] if m.lower() in synth_stats else synth_stats.get(m, 0)
        if r > 0:
            score += ((s - r) / r) ** 2
    return score

print("=== LEVEL 4 HMM GENERATOR: fitting to real statistics ===\n")
for label, lines in [('A', lines_A), ('B', lines_B)]:
    real_s = full_stats(lines)
    print(f"Language {label} -- REAL:")
    print(f"  H1={real_s['H1']:.3f}  TTR={real_s['ttr']:.3f}  avglen={real_s['avglen']:.2f}"
          f"  doubling={real_s['doubling']*100:.3f}%  asym={real_s['asym']:.3f}")

    best = None
    for p_stick in [0.0, 0.002, 0.004, 0.006, 0.008, 0.010, 0.015]:
        synth_lines = generate_hmm_corpus(lines, p_stick, seed=42)
        synth_s = full_stats(synth_lines)
        score = fit_score(
            {'h1': real_s['H1'], 'ttr': real_s['ttr'], 'avglen': real_s['avglen'],
             'doubling': real_s['doubling'], 'asym': real_s['asym']},
            {'h1': synth_s['H1'], 'ttr': synth_s['ttr'], 'avglen': synth_s['avglen'],
             'doubling': synth_s['doubling'], 'asym': synth_s['asym']}
        )
        if best is None or score < best[0]:
            best = (score, p_stick, synth_s)

    score, p_stick, synth_s = best
    print(f"  BEST p_stick={p_stick} (composite fit score={score:.4f}):")
    print(f"  H1={synth_s['H1']:.3f}  TTR={synth_s['ttr']:.3f}  avglen={synth_s['avglen']:.2f}"
          f"  doubling={synth_s['doubling']*100:.3f}%  asym={synth_s['asym']:.3f}")

    # Compare improvement over Level 3 (sticky only)
    print(f"\n  IMPROVEMENT vs Level 3 (sticky only, no class ordering):")
    print(f"  TTR: Level 3 was ~0.231 (A) / 0.248 (B), Level 4 = {synth_s['ttr']:.3f}")
    print(f"  Asym: Level 3 had no ordering structure (≈ null), Level 4 = {synth_s['asym']:.3f}")
    print()
