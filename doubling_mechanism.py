import re
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

def analyze_doubling_mechanism(lines, label):
    print(f"\n{'='*60}\nLanguage {label}\n{'='*60}")

    # 1. WHICH WORDS double most often?
    doubled_words = Counter()
    total_pairs = 0
    for line in lines:
        for i in range(len(line)-1):
            total_pairs += 1
            if line[i] == line[i+1]:
                doubled_words[line[i]] += 1
    print(f"\nTotal doubling events: {sum(doubled_words.values())}")
    print(f"Distinct words that double: {len(doubled_words)}")
    print(f"Top doubled words: {doubled_words.most_common(10)}")

    # 2. POSITIONAL distribution: where in the line does doubling occur?
    # bucket: position of the FIRST word of the doubled pair, as fraction of line length
    position_buckets = Counter()  # 'initial', 'medial', 'final'
    for line in lines:
        n = len(line)
        if n < 2:
            continue
        for i in range(n-1):
            if line[i] == line[i+1]:
                frac = i / max(n-2, 1)  # 0 = very start, 1 = very end
                if frac < 0.34:
                    position_buckets['initial_third'] += 1
                elif frac < 0.67:
                    position_buckets['middle_third'] += 1
                else:
                    position_buckets['final_third'] += 1
    print(f"\nPositional distribution of doubling events (by third of line):")
    total_doub = sum(position_buckets.values())
    for bucket in ['initial_third', 'middle_third', 'final_third']:
        cnt = position_buckets.get(bucket, 0)
        pct = 100*cnt/total_doub if total_doub else 0
        print(f"  {bucket}: {cnt} ({pct:.1f}%)")

    # 3. Compare to where WORDS in general fall (baseline expectation if doubling were positionally uniform)
    general_position_buckets = Counter()
    for line in lines:
        n = len(line)
        if n < 2:
            continue
        for i in range(n-1):
            frac = i / max(n-2, 1)
            if frac < 0.34:
                general_position_buckets['initial_third'] += 1
            elif frac < 0.67:
                general_position_buckets['middle_third'] += 1
            else:
                general_position_buckets['final_third'] += 1
    total_gen = sum(general_position_buckets.values())
    print(f"\nFor comparison, positional distribution of ALL adjacent-pair START positions (baseline):")
    for bucket in ['initial_third', 'middle_third', 'final_third']:
        cnt = general_position_buckets.get(bucket, 0)
        pct = 100*cnt/total_gen if total_gen else 0
        print(f"  {bucket}: {cnt} ({pct:.1f}%)")

    # 4. Line length effect: do doubling events happen more in LONGER lines (more chances) 
    #    or is the rate (per adjacent pair) elevated even controlling for length?
    short_lines = [l for l in lines if len(l) <= 5]
    long_lines = [l for l in lines if len(l) > 5]
    def rate(lines_subset):
        pairs = sum(max(len(l)-1,0) for l in lines_subset)
        reps = sum(1 for l in lines_subset for i in range(len(l)-1) if l[i]==l[i+1])
        return reps, pairs, (reps/pairs if pairs else 0)
    sr, sp, srate = rate(short_lines)
    lr, lp, lrate = rate(long_lines)
    print(f"\nShort lines (<=5 words): {srate*100:.3f}% doubling rate ({sr}/{sp})")
    print(f"Long lines (>5 words):  {lrate*100:.3f}% doubling rate ({lr}/{lp})")

for label, lines in [('A', lines_A), ('B', lines_B)]:
    analyze_doubling_mechanism(lines, label)
