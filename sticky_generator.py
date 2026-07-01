import re, math, random
from collections import Counter

def parse_fsg_with_lines(path):
    records = []
    cur_lang = None; cur_section = None; cur_folio = None
    cur_lines = []; cur_line_words = []
    def flush_line():
        nonlocal cur_line_words
        if cur_line_words:
            cur_lines.append(cur_line_words)
            cur_line_words = []
    def flush_folio():
        flush_line()
        if cur_lines and cur_folio:
            records.append({'folio': cur_folio, 'lang': cur_lang, 'section': cur_section, 'lines': [l[:] for l in cur_lines]})
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
        words_here = [w.strip() for w in text.split(',') if w.strip()]
        if words_here:
            cur_line_words.extend(words_here)
        flush_line()
    flush_folio()
    return records

recs = parse_fsg_with_lines('raw_fsg.txt')
lines_A, lines_B = [], []
for r in recs:
    if r['lang'] == 'A': lines_A.extend(r['lines'])
    elif r['lang'] == 'B': lines_B.extend(r['lines'])

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

def doubling_rate(lines):
    pairs = 0; reps = 0
    for line in lines:
        for i in range(len(line)-1):
            pairs += 1
            if line[i] == line[i+1]:
                reps += 1
    return reps/pairs if pairs else 0

def generate_sticky_corpus(lines_real, stick_prob, seed=42):
    """Sample words with replacement from the real vocabulary distribution,
    but with probability `stick_prob`, force-repeat the previous word instead
    of drawing a fresh one. Calibrate stick_prob to match real doubling rate."""
    rng = random.Random(seed)
    flat_real = [w for line in lines_real for w in line]
    line_lens = [len(l) for l in lines_real]
    out_lines = []
    prev_word = None
    for ln in line_lens:
        line_out = []
        for i in range(ln):
            if prev_word is not None and rng.random() < stick_prob:
                w = prev_word
            else:
                w = rng.choice(flat_real)
            line_out.append(w)
            prev_word = w
        out_lines.append(line_out)
    return out_lines

print("=== STICKY BAG-OF-WORDS MODEL: calibrating stick_prob to match real doubling rate ===")
for label, lines in [('A', lines_A), ('B', lines_B)]:
    real_words = [w for line in lines for w in line]
    real_stats = full_stats(real_words)
    real_doubling = doubling_rate(lines)

    print(f"\nLanguage {label}:")
    print(f"  REAL: TTR={real_stats['ttr']:.3f} H0={real_stats['H0']:.3f} H1={real_stats['H1']:.3f} "
          f"avglen={real_stats['avglen']:.2f}  doubling={real_doubling*100:.3f}%")

    # try a range of stick_prob values and find the one that best matches real doubling rate
    best = None
    for stick_prob in [0.0, 0.002, 0.004, 0.006, 0.008, 0.01, 0.012, 0.015, 0.02]:
        synth_lines = generate_sticky_corpus(lines, stick_prob, seed=42)
        synth_words = [w for line in synth_lines for w in line]
        synth_stats = full_stats(synth_words)
        synth_doubling = doubling_rate(synth_lines)
        diff = abs(synth_doubling - real_doubling)
        if best is None or diff < best[0]:
            best = (diff, stick_prob, synth_stats, synth_doubling)

    diff, stick_prob, synth_stats, synth_doubling = best
    print(f"  BEST-FIT stick_prob={stick_prob}:")
    print(f"  SYNTH: TTR={synth_stats['ttr']:.3f} H0={synth_stats['H0']:.3f} H1={synth_stats['H1']:.3f} "
          f"avglen={synth_stats['avglen']:.2f}  doubling={synth_doubling*100:.3f}%")
