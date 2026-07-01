import re
from collections import defaultdict

def parse_fsg(path):
    """Parse the Currier/FSG transliteration format with # metadata comments."""
    records = []  # list of dicts: {lang, hand, section, folio, words}
    cur_lang = None
    cur_section = None
    cur_folio = None
    cur_words = []

    def flush():
        if cur_words and cur_folio:
            records.append({
                'folio': cur_folio,
                'lang': cur_lang,
                'section': cur_section,
                'words': list(cur_words)
            })

    with open(path, encoding='utf-8', errors='replace') as f:
        lines = f.readlines()

    for raw in lines:
        line = raw.rstrip('\n')
        stripped = line.strip()

        if stripped.startswith('#'):
            comment = stripped.lstrip('#').strip()
            low = comment.lower()
            if low.startswith('folio'):
                # new folio -> flush previous record
                flush()
                cur_words = []
                cur_folio = comment.split(None,1)[1].strip() if len(comment.split(None,1))>1 else comment
            if "language a" in low or "currier's language a" in low:
                cur_lang = 'A'
            elif "language b" in low or "currier's language b" in low:
                cur_lang = 'B'
            if 'herbal' in low:
                cur_section = 'herbal'
            elif 'biological' in low:
                cur_section = 'biological'
            elif 'pharma' in low or 'phamaceutical' in low:
                cur_section = 'pharmaceutical'
            elif 'star' in low:
                cur_section = 'stars'
            elif 'cosmological' in low:
                cur_section = 'cosmological'
            elif 'astronom' in low:
                cur_section = 'astronomical'
            elif 'text only' in low:
                # don't overwrite a real section with "text only" unless none set yet
                if cur_section is None:
                    cur_section = 'text_only'
            continue

        if not stripped:
            continue

        # strip variant-reading parens (A|B) -> just take first option A
        # remove the {...} bracket comments
        text = re.sub(r'\{[^}]*\}', '', stripped)
        # remove trailing - or = continuation markers
        text = text.rstrip('-=')
        # resolve (X|Y) -> X  (take first reading)
        text = re.sub(r'\(([^|)]*)\|[^)]*\)', r'\1', text)
        # words separated by commas in this format
        for w in text.split(','):
            w = w.strip()
            if w and not w.startswith('#'):
                cur_words.append(w)

    flush()
    return records

recs = parse_fsg('raw_fsg.txt')
print(f"Total folio-records parsed: {len(recs)}")
total_words = sum(len(r['words']) for r in recs)
print(f"Total words: {total_words}")

by_lang = defaultdict(int)
by_section = defaultdict(int)
for r in recs:
    by_lang[r['lang']] += len(r['words'])
    by_section[r['section']] += len(r['words'])

print("\nWords by language tag:")
for k,v in by_lang.items():
    print(f"  {k}: {v}")

print("\nWords by section tag:")
for k,v in by_section.items():
    print(f"  {k}: {v}")

print("\nSample folios parsed:", [r['folio'] for r in recs[:10]])
