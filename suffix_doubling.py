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

def get_doubled_and_nondoubled_words(lines):
    """Return (set of words that ever appear doubled, Counter of ALL words with their total frequency)"""
    doubled_words = set()
    all_word_freq = Counter()
    for line in lines:
        for w in line:
            all_word_freq[w] += 1
        for i in range(len(line)-1):
            if line[i] == line[i+1]:
                doubled_words.add(line[i])
    return doubled_words, all_word_freq

def suffix_analysis(words_set_or_counter, label, top_n=10):
    """Look at common SUFFIXES (last 2-3 chars) among the given words."""
    suffix2 = Counter()
    suffix3 = Counter()
    for w in words_set_or_counter:
        if len(w) >= 2:
            suffix2[w[-2:]] += 1
        if len(w) >= 3:
            suffix3[w[-3:]] += 1
    print(f"  Top 2-char suffixes ({label}): {suffix2.most_common(top_n)}")
    print(f"  Top 3-char suffixes ({label}): {suffix3.most_common(top_n)}")

for label, lines in [('A', lines_A), ('B', lines_B)]:
    print(f"\n{'='*70}\nLanguage {label}\n{'='*70}")
    doubled_words, all_freq = get_doubled_and_nondoubled_words(lines)
    nondoubled_words = set(all_freq.keys()) - doubled_words

    print(f"\nDistinct words that EVER double: {len(doubled_words)}")
    print(f"Distinct words that NEVER double: {len(nondoubled_words)}")

    print(f"\n--- Suffix profile of WORDS THAT DOUBLE ---")
    suffix_analysis(doubled_words, "doubling words")

    print(f"\n--- Suffix profile of ALL WORDS (baseline) ---")
    suffix_analysis(all_freq.keys(), "all words")

    # Specifically: what % of doubled words end in each of the most common suffixes,
    # vs what % of ALL words end in those suffixes (controlling for the fact that
    # doubling words are drawn from the high-frequency tail)
    print(f"\n--- Do doubling words skew toward any particular suffix, beyond what frequency alone predicts? ---")
    # Compare: among words with frequency >= 5 (i.e., comparable "could-plausibly-double" pool),
    # what fraction actually double, broken down by suffix
    high_freq_words = {w for w,c in all_freq.items() if c >= 5}
    high_freq_doubled = high_freq_words & doubled_words
    print(f"Words with freq>=5: {len(high_freq_words)} total, {len(high_freq_doubled)} of them double "
          f"({100*len(high_freq_doubled)/len(high_freq_words):.1f}%)")

    suffix_rate = defaultdict(lambda: [0,0])  # suffix -> [doubled_count, total_count]
    for w in high_freq_words:
        suf = w[-2:] if len(w) >= 2 else w
        suffix_rate[suf][1] += 1
        if w in doubled_words:
            suffix_rate[suf][0] += 1
    print("Doubling rate by 2-char suffix (suffixes with >=5 high-freq words):")
    for suf, (d, t) in sorted(suffix_rate.items(), key=lambda x: -x[1][1]):
        if t >= 5:
            print(f"    -{suf}: {d}/{t} = {100*d/t:.1f}%")
