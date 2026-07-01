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

def classify_word(w, suffix_len=2):
    if len(w) < suffix_len: return w
    return w[-suffix_len:]

def get_class_freqs(lines, suffix_len=2):
    counts = Counter()
    for line in lines:
        for w in line:
            counts[classify_word(w, suffix_len)] += 1
    return counts

def pairwise_asymmetry_filtered(lines, classes, class_freqs, suffix_len=2, min_total=10, max_freq_ratio=3.0):
    """Same as before, but EXCLUDE pairs where one class is much more frequent
    than the other (freq_ratio > max_freq_ratio) -- this isolates pairs of
    COMPARABLY FREQUENT classes, removing the 'rare class = noisy estimate'
    confound."""
    class_set = set(classes)
    pair_counts = Counter()
    for line in lines:
        tags = [classify_word(w, suffix_len) for w in line]
        for i in range(len(tags)-1):
            a, b = tags[i], tags[i+1]
            if a in class_set and b in class_set:
                pair_counts[(a,b)] += 1
    results = []
    for i, x in enumerate(classes):
        for y in classes[i+1:]:
            fx, fy = class_freqs[x], class_freqs[y]
            ratio = max(fx,fy)/min(fx,fy) if min(fx,fy) > 0 else float('inf')
            if ratio > max_freq_ratio:
                continue  # skip lopsided-frequency pairs
            xy = pair_counts.get((x,y), 0)
            yx = pair_counts.get((y,x), 0)
            total = xy + yx
            if total >= min_total:
                asym = (xy - yx) / total
                results.append(abs(asym))
    return results

def shuffle_lines(lines, seed):
    rng = random.Random(seed)
    flat = [w for line in lines for w in line]
    rng.shuffle(flat)
    out = []
    idx = 0
    for line in lines:
        out.append(flat[idx:idx+len(line)])
        idx += len(line)
    return out

for label, lines in [('A', lines_A), ('B', lines_B)]:
    print(f"\n{'='*60}\nLanguage {label} -- FREQUENCY-MATCHED PAIRS ONLY (ratio <= 3x)\n{'='*60}")
    class_freqs = get_class_freqs(lines)
    top_classes = [c for c,_ in class_freqs.most_common(15)]  # widen pool since we're filtering

    real_asyms = pairwise_asymmetry_filtered(lines, top_classes, class_freqs)
    if not real_asyms:
        print("No pairs survived the frequency-matching filter -- inconclusive.")
        continue
    real_avg = sum(real_asyms)/len(real_asyms)
    print(f"Real average |asymmetry| ({len(real_asyms)} freq-matched pairs): {real_avg:.4f}")

    n_trials = 200
    shuf_avgs = []
    for t in range(n_trials):
        shuf = shuffle_lines(lines, seed=t)
        shuf_freqs = get_class_freqs(shuf)  # same words, same freqs, just reordered -- freqs identical to real
        shuf_asyms = pairwise_asymmetry_filtered(shuf, top_classes, class_freqs)  # use REAL freqs for filtering (freqs are invariant to shuffle anyway)
        if shuf_asyms:
            shuf_avgs.append(sum(shuf_asyms)/len(shuf_asyms))

    shuf_mean = sum(shuf_avgs)/len(shuf_avgs)
    shuf_sd = math.sqrt(sum((x-shuf_mean)**2 for x in shuf_avgs)/len(shuf_avgs))
    z = (real_avg - shuf_mean)/shuf_sd if shuf_sd > 0 else float('inf')
    p_empirical = sum(1 for x in shuf_avgs if x >= real_avg) / len(shuf_avgs)

    print(f"Null distribution ({n_trials} shuffles): mean={shuf_mean:.4f}, sd={shuf_sd:.4f}")
    print(f"Z-score: {z:.2f}   Empirical p-value: {p_empirical:.4f}")
