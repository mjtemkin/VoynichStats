import re, math, random
from collections import Counter, defaultdict

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
    """Word class = its last `suffix_len` characters (proxy for grammatical role,
    consistent with Stolfi's prefix-stem-suffix grammar hypothesis)."""
    if len(w) < suffix_len:
        return w
    return w[-suffix_len:]

def get_top_classes(lines, n_classes=10, suffix_len=2):
    counts = Counter()
    for line in lines:
        for w in line:
            counts[classify_word(w, suffix_len)] += 1
    return [c for c, _ in counts.most_common(n_classes)]

def pairwise_asymmetry(lines, classes, suffix_len=2):
    """For each ordered pair of classes (X, Y), count how often X immediately
    precedes Y within a line, vs Y immediately precedes X. Compute an asymmetry
    score = (XY - YX) / (XY + YX) for each unordered pair; ranges from -1
    (always Y-then-X) to +1 (always X-then-Y); near 0 = symmetric/no preference."""
    class_set = set(classes)
    pair_counts = Counter()  # (classX, classY) -> count of X immediately followed by Y
    for line in lines:
        tags = [classify_word(w, suffix_len) for w in line]
        for i in range(len(tags)-1):
            a, b = tags[i], tags[i+1]
            if a in class_set and b in class_set:
                pair_counts[(a,b)] += 1
    results = []
    for i, x in enumerate(classes):
        for y in classes[i+1:]:
            xy = pair_counts.get((x,y), 0)
            yx = pair_counts.get((y,x), 0)
            total = xy + yx
            if total >= 10:  # only report pairs with enough data
                asym = (xy - yx) / total
                results.append((abs(asym), asym, x, y, xy, yx, total))
    return sorted(results, reverse=True)

def shuffle_lines(lines, seed=42):
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
    print(f"\n{'='*70}\nLanguage {label}\n{'='*70}")
    classes = get_top_classes(lines, n_classes=10)
    print(f"Top 10 word-classes (by 2-char suffix): {classes}")

    real_results = pairwise_asymmetry(lines, classes)
    print(f"\nTop 8 most asymmetric class-pairs (REAL data):")
    print(f"{'|asym|':>8}{'asym':>8}{'X->Y':>10}{'Y->X':>10}{'X':>6}{'Y':>6}{'total':>8}")
    for absasym, asym, x, y, xy, yx, total in real_results[:8]:
        print(f"{absasym:>8.3f}{asym:>8.3f}{xy:>10}{yx:>10}{x:>6}{y:>6}{total:>8}")

    shuffled = shuffle_lines(lines)
    shuf_results = pairwise_asymmetry(shuffled, classes)
    print(f"\nSAME class-pairs in SHUFFLED data (null baseline):")
    print(f"{'|asym|':>8}{'asym':>8}{'X->Y':>10}{'Y->X':>10}{'X':>6}{'Y':>6}{'total':>8}")
    shuf_lookup = {(x,y): (absasym, asym, xy, yx, total) for absasym, asym, x, y, xy, yx, total in shuf_results}
    for absasym, asym, x, y, xy, yx, total in real_results[:8]:
        if (x,y) in shuf_lookup:
            s_abs, s_asym, s_xy, s_yx, s_total = shuf_lookup[(x,y)]
            print(f"{s_abs:>8.3f}{s_asym:>8.3f}{s_xy:>10}{s_yx:>10}{x:>6}{y:>6}{s_total:>8}")
        else:
            print(f"  (pair {x}-{y} not found in shuffled top pairs)")

    # Summary stat: average |asymmetry| across all sufficiently-sampled pairs, real vs shuffled
    avg_real = sum(r[0] for r in real_results) / len(real_results) if real_results else 0
    avg_shuf = sum(r[0] for r in shuf_results) / len(shuf_results) if shuf_results else 0
    print(f"\nAVERAGE |asymmetry| across all {len(real_results)} pairs: REAL={avg_real:.3f}  SHUFFLED={avg_shuf:.3f}")
