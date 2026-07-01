import re, random, math
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
groups = {}
for r in recs:
    if r['lang'] and r['section']:
        key = (r['lang'], r['section'])
        groups.setdefault(key, []).extend(r['lines'])

def doubling_stats(lines, n_shuffle_trials=30, seed=42):
    pairs = 0; reps = 0
    for line in lines:
        for i in range(len(line)-1):
            pairs += 1
            if line[i] == line[i+1]:
                reps += 1
    rate = reps/pairs if pairs else 0
    rng = random.Random(seed)
    flat = [w for line in lines for w in line]
    lens = [len(l) for l in lines]
    shuf_rates = []
    for _ in range(n_shuffle_trials):
        shuf = flat[:]; rng.shuffle(shuf)
        idx=0; sreps=0; spairs=0
        for ln in lens:
            seg = shuf[idx:idx+ln]; idx+=ln
            for i in range(len(seg)-1):
                spairs+=1
                if seg[i]==seg[i+1]: sreps+=1
        shuf_rates.append(sreps/spairs if spairs else 0)
    shuf_avg = sum(shuf_rates)/len(shuf_rates)
    se = math.sqrt(rate*(1-rate)/pairs) if pairs and 0 < rate < 1 else float('nan')
    return reps, pairs, rate, shuf_avg, se

print(f"{'Group':<22}{'Pairs':>7}{'Reps':>6}{'Real%':>8}{'Shuf%':>8}{'Ratio':>7}{'SE(pp)':>8}")
for key in [('A','herbal'), ('B','herbal'), ('B','biological'), ('A','pharmaceutical'), ('B','stars')]:
    if key not in groups:
        print(f"{key}: NO DATA")
        continue
    lines = groups[key]
    reps, pairs, rate, shuf, se = doubling_stats(lines)
    ratio = rate/shuf if shuf > 0 else float('nan')
    label = f"{key[0]}/{key[1]}"
    print(f"{label:<22}{pairs:>7}{reps:>6}{rate*100:>7.3f}%{shuf*100:>7.3f}%{ratio:>6.2f}x{se*100:>7.3f}")
