import re, random
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

def immediate_repeat_stats(lines):
    """Count how often word[i] == word[i+1] within the same line (real adjacency)."""
    total_adjacent_pairs = 0
    exact_repeats = 0
    for line in lines:
        for i in range(len(line)-1):
            total_adjacent_pairs += 1
            if line[i] == line[i+1]:
                exact_repeats += 1
    rate = exact_repeats/total_adjacent_pairs if total_adjacent_pairs else 0
    return exact_repeats, total_adjacent_pairs, rate

def expected_repeat_rate(lines):
    """What repeat rate would we expect by CHANCE given the real word-frequency distribution?
    (sum of p_i^2 over the vocabulary -- the 'collision probability')"""
    flat = [w for line in lines for w in line]
    counts = Counter(flat)
    n = len(flat)
    return sum((c/n)**2 for c in counts.values())

def shuffled_repeat_rate(lines, seed=42, n_trials=20):
    rng = random.Random(seed)
    flat = [w for line in lines for w in line]
    line_lens = [len(l) for l in lines]
    rates = []
    for trial in range(n_trials):
        shuf = flat[:]
        rng.shuffle(shuf)
        idx = 0
        reps = 0
        pairs = 0
        for ln in line_lens:
            seg = shuf[idx:idx+ln]
            idx += ln
            for i in range(len(seg)-1):
                pairs += 1
                if seg[i] == seg[i+1]:
                    reps += 1
        rates.append(reps/pairs if pairs else 0)
    return sum(rates)/len(rates)

print("=== IMMEDIATE WORD REPETITION (word[i] == word[i+1], same line) ===")
for label, lines in [('A', lines_A), ('B', lines_B)]:
    reps, pairs, rate = immediate_repeat_stats(lines)
    expected_chance = expected_repeat_rate(lines)
    shuf_rate = shuffled_repeat_rate(lines)
    print(f"\nLanguage {label}:")
    print(f"  REAL adjacent-repeat rate:      {rate*100:.3f}%  ({reps} repeats / {pairs} adjacent pairs)")
    print(f"  Expected from word frequencies: {expected_chance*100:.3f}%  (sum of p_i^2, i.e. 'collision' baseline)")
    print(f"  SHUFFLED lines repeat rate:     {shuf_rate*100:.3f}%  (avg of 20 shuffles, same line lengths)")
    print(f"  Real / Shuffled ratio: {rate/shuf_rate:.2f}x" if shuf_rate > 0 else "  n/a")
