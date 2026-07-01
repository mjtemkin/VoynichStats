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

def doubling_rate(lines):
    pairs = 0; reps = 0
    for line in lines:
        for i in range(len(line)-1):
            pairs += 1
            if line[i] == line[i+1]:
                reps += 1
    return reps, pairs, (reps/pairs if pairs else 0)

def shuffle_WITHIN_EACH_LINE(lines, seed=42):
    """Scramble word order WITHIN each line only -- local scramble.
    This tests: does doubling depend on the SPECIFIC scribal sequence within
    a line, or just on which words happen to co-occur in the same line?"""
    rng = random.Random(seed)
    out = []
    for line in lines:
        shuffled = line[:]
        rng.shuffle(shuffled)
        out.append(shuffled)
    return out

def shuffle_GLOBALLY(lines, seed=42):
    """Full global shuffle (our original control) -- destroys ALL local structure,
    including which words co-occur in the same line."""
    rng = random.Random(seed)
    flat = [w for line in lines for w in line]
    rng.shuffle(flat)
    out = []
    idx = 0
    for line in lines:
        out.append(flat[idx:idx+len(line)])
        idx += len(line)
    return out

def run_trials(lines, shuffle_fn, n_trials=30, seed_base=0):
    rates = []
    for t in range(n_trials):
        shuffled = shuffle_fn(lines, seed=seed_base + t)
        _, _, rate = doubling_rate(shuffled)
        rates.append(rate)
    return sum(rates)/len(rates), rates

print("=== COMPARING THREE CONDITIONS: REAL ORDER vs WITHIN-LINE SHUFFLE vs FULL GLOBAL SHUFFLE ===")
for label, lines in [('A', lines_A), ('B', lines_B)]:
    real_reps, real_pairs, real_rate = doubling_rate(lines)
    within_avg, within_rates = run_trials(lines, shuffle_WITHIN_EACH_LINE)
    global_avg, global_rates = run_trials(lines, shuffle_GLOBALLY)

    print(f"\nLanguage {label}:")
    print(f"  REAL (scribal order):        {real_rate*100:.3f}%  ({real_reps}/{real_pairs})")
    print(f"  WITHIN-LINE shuffle (avg of 30): {within_avg*100:.3f}%   <- same words co-occur in same line, order scrambled")
    print(f"  GLOBAL shuffle (avg of 30):      {global_avg*100:.3f}%   <- words redistributed across ALL lines")
    print(f"  Real vs within-line ratio: {real_rate/within_avg:.2f}x" if within_avg > 0 else "  n/a")
    print(f"  Real vs global ratio:      {real_rate/global_avg:.2f}x" if global_avg > 0 else "  n/a")
    print(f"  Within-line vs global ratio: {within_avg/global_avg:.2f}x" if global_avg > 0 else "  n/a")
