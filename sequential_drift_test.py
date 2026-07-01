import re, math
from collections import Counter

def parse_fsg_ordered(path):
    """Parse preserving ORIGINAL FILE ORDER (which follows folio order), 
    returning a flat list of (folio, lang, section, line_words) in sequence."""
    records = []
    cur_lang = None; cur_section = None; cur_folio = None
    cur_line_words = []
    def flush_line():
        nonlocal cur_line_words
        if cur_line_words:
            records.append({'folio': cur_folio, 'lang': cur_lang, 'section': cur_section, 'words': cur_line_words[:]})
            cur_line_words = []
    with open(path, encoding='utf-8', errors='replace') as f:
        raw_lines = f.readlines()
    for raw in raw_lines:
        line = raw.rstrip('\n'); stripped = line.strip()
        if stripped.startswith('#'):
            comment = stripped.lstrip('#').strip(); low = comment.lower()
            if low.startswith('folio'):
                flush_line()
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
    flush_line()
    return records

recs = parse_fsg_ordered('raw_fsg.txt')
print(f"Total ordered line-records: {len(recs)}")
print(f"Folio sequence (first 5, last 5): {[r['folio'] for r in recs[:5]]} ... {[r['folio'] for r in recs[-5:]]}")

# Flatten into one long sequence of words, remembering line boundaries AND folio/section for each word
flat_words = []
flat_meta = []  # (folio, lang, section) per word, plus a marker for line-start
for r in recs:
    for i, w in enumerate(r['words']):
        flat_words.append(w)
        flat_meta.append((r['folio'], r['lang'], r['section'], i == 0))

print(f"Total words in sequence: {len(flat_words)}")

# Sliding window doubling rate (within-line adjacency only -- use line boundaries)
window_size = 800  # words per window
step = 400  # overlap

def doubling_rate_in_range(start_idx, end_idx):
    """Compute doubling rate among words[start_idx:end_idx], respecting line boundaries
    (don't count a 'double' across a line break)."""
    reps = 0; pairs = 0
    for i in range(start_idx, min(end_idx, len(flat_words)-1)):
        # skip if word i+1 is the start of a new line (no real adjacency across line break)
        if flat_meta[i+1][3]:  # is_line_start
            continue
        pairs += 1
        if flat_words[i] == flat_words[i+1]:
            reps += 1
    return reps, pairs, (reps/pairs if pairs else 0)

print(f"\n=== SLIDING WINDOW DOUBLING RATE (window={window_size} words, step={step}) ===")
print(f"{'Start':>7}{'End':>7}{'Folios':>20}{'Lang(s)':>10}{'Section(s)':>30}{'Reps':>6}{'Pairs':>7}{'Rate':>8}")
idx = 0
results = []
while idx < len(flat_words):
    end = min(idx + window_size, len(flat_words))
    reps, pairs, rate = doubling_rate_in_range(idx, end)
    folios_in_window = sorted(set(flat_meta[i][0] for i in range(idx, end)), key=lambda f: (len(f), f))
    langs_in_window = sorted(set(flat_meta[i][1] for i in range(idx, end) if flat_meta[i][1]))
    sections_in_window = sorted(set(flat_meta[i][2] for i in range(idx, end) if flat_meta[i][2]))
    folio_range = f"{folios_in_window[0]}-{folios_in_window[-1]}" if folios_in_window else "?"
    results.append((idx, end, folio_range, langs_in_window, sections_in_window, reps, pairs, rate))
    print(f"{idx:>7}{end:>7}{folio_range:>20}{str(langs_in_window):>10}{str(sections_in_window):>30}{reps:>6}{pairs:>7}{rate*100:>7.3f}%")
    idx += step
    if end >= len(flat_words):
        break
