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

# Separate by language first -- we compare sections within each language
def doubling_rate(lines):
    pairs = reps = 0
    for line in lines:
        for i in range(len(line)-1):
            pairs += 1
            if line[i] == line[i+1]:
                reps += 1
    return reps, pairs, (reps/pairs if pairs else 0)

def shuffled_chance(lines, n=1):
    """Chance baseline from word frequencies."""
    flat = [w for line in lines for w in line]
    counts = Counter(flat); total = len(flat)
    return sum((c/total)**2 for c in counts.values())

def per_section_rates(recs, lang):
    by_section = defaultdict(list)
    for r in recs:
        if r['lang'] == lang and r['section']:
            by_section[r['section']].extend(r['lines'])
    results = {}
    for sec, lines in by_section.items():
        reps, pairs, rate = doubling_rate(lines)
        chance = shuffled_chance(lines)
        if pairs >= 500:  # only sections with meaningful sample size
            results[sec] = dict(rate=rate, chance=chance, ratio=rate/chance if chance else 0,
                              reps=reps, pairs=pairs)
    return results

print("=== OBSERVED SECTION DOUBLING RATIOS ===")
for lang in ['A', 'B']:
    print(f"\nLanguage {lang}:")
    sec_rates = per_section_rates(recs, lang)
    for sec, s in sorted(sec_rates.items(), key=lambda x: -x[1]['ratio']):
        print(f"  {sec:<20} {s['ratio']:.3f}x chance  ({s['reps']}/{s['pairs']} pairs)")
    ratios = [s['ratio'] for s in sec_rates.values()]
    if len(ratios) >= 2:
        observed_gap = max(ratios) - min(ratios)
        print(f"  Max-min gap: {observed_gap:.3f}")

# ===== PERMUTATION TEST =====
# Within each language: shuffle ALL words across ALL lines while preserving
# line-lengths and section membership of lines (i.e., keep the assignment of
# lines to sections fixed, shuffle only the WORD CONTENT within each line-slot)
# This destroys real word-sequence but preserves section structure and line sizes.
def permutation_gap(recs, lang, seed):
    rng = random.Random(seed)
    # Build section -> lines lookup with real structure
    by_section = defaultdict(list)
    for r in recs:
        if r['lang'] == lang and r['section']:
            by_section[r['section']].extend(r['lines'])
    # flatten ALL words from this language, shuffle, re-distribute into same line-slots
    all_lines_by_section = {sec: lines for sec, lines in by_section.items()
                           if sum(len(l) for l in lines) >= 500}
    all_words = [w for lines in all_lines_by_section.values()
                 for line in lines for w in line]
    rng.shuffle(all_words)
    # re-fill lines in the same order
    idx = 0
    new_by_section = {}
    for sec, lines in all_lines_by_section.items():
        new_lines = []
        for line in lines:
            new_lines.append(all_words[idx:idx+len(line)])
            idx += len(line)
        new_by_section[sec] = new_lines
    # compute per-section doubling ratio in shuffled data
    ratios = []
    for sec, lines in new_by_section.items():
        reps, pairs, rate = doubling_rate(lines)
        chance = shuffled_chance(lines)
        if pairs >= 500 and chance > 0:
            ratios.append(rate/chance)
    if len(ratios) < 2:
        return 0
    return max(ratios) - min(ratios)

print("\n=== PERMUTATION TEST: Is the section gap larger than expected by chance? ===")
n_trials = 500
for lang in ['A', 'B']:
    sec_rates = per_section_rates(recs, lang)
    ratios = [s['ratio'] for s in sec_rates.values()]
    if len(ratios) < 2:
        print(f"Language {lang}: not enough sections with adequate sample size")
        continue
    observed_gap = max(ratios) - min(ratios)
    null_gaps = [permutation_gap(recs, lang, seed=t) for t in range(n_trials)]
    null_mean = sum(null_gaps)/len(null_gaps)
    null_sd = math.sqrt(sum((x-null_mean)**2 for x in null_gaps)/len(null_gaps))
    z = (observed_gap - null_mean)/null_sd if null_sd > 0 else float('inf')
    p = sum(1 for x in null_gaps if x >= observed_gap)/len(null_gaps)
    print(f"\nLanguage {lang}:")
    print(f"  Observed max-min gap: {observed_gap:.3f}")
    print(f"  Null distribution ({n_trials} permutations): mean={null_mean:.3f}, sd={null_sd:.4f}")
    print(f"  Z-score: {z:.2f}  Empirical p-value: {p:.4f}")
    if p < 0.01:
        print(f"  --> The cross-section gap is LARGER than expected by chance alone")
        print(f"      (sections are behaving genuinely differently, not just noisy estimates)")
    else:
        print(f"  --> The cross-section gap is WITHIN the range expected from sampling noise")
        print(f"      (one stationary process, section differences are just noise)")
