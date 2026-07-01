import re
from collections import Counter

def parse_fsg(path):
    records = []
    cur_lang = None; cur_section = None; cur_folio = None; cur_words = []
    def flush():
        if cur_words and cur_folio:
            records.append({'folio': cur_folio, 'lang': cur_lang, 'section': cur_section, 'words': list(cur_words)})
    with open(path, encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    for raw in lines:
        line = raw.rstrip('\n'); stripped = line.strip()
        if stripped.startswith('#'):
            comment = stripped.lstrip('#').strip(); low = comment.lower()
            if low.startswith('folio'):
                flush(); cur_words = []
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
        for w in text.split(','):
            w = w.strip()
            if w: cur_words.append(w)
    flush()
    return records

recs = parse_fsg('raw_fsg.txt')
all_words = []
for r in recs:
    all_words.extend(r['words'])

corpus = ''.join(all_words)
char_freq = Counter(corpus)
total = sum(char_freq.values())

print("=== VOYNICHESE CHARACTER FREQUENCY (this transliteration alphabet) ===")
for ch, cnt in char_freq.most_common(20):
    print(f"  {ch}: {cnt} ({100*cnt/total:.2f}%)")
print(f"\nAlphabet size: {len(char_freq)} distinct characters")
print(f"Total characters: {total}")

# Known English letter frequency (standard reference table, approx, descending)
english_freq_order = list("etaoinshrdlcumwfgypbvkjxqz")
# Known Latin letter frequency (approximate, descending) -- Latin texts of this era
latin_freq_order = list("eiatusnrlcdmoqpbgvfhxyzk")

voynich_freq_order = [ch for ch, cnt in char_freq.most_common()]

print(f"\nVoynichese chars by frequency rank: {voynich_freq_order}")
print(f"English letters by frequency rank:  {english_freq_order}")
print(f"Latin letters by frequency rank:    {latin_freq_order}")

def apply_substitution(words, mapping):
    out = []
    for w in words:
        out.append(''.join(mapping.get(c, '?') for c in w))
    return out

# Build rank-for-rank substitution mappings
voy_to_eng = {v: e for v, e in zip(voynich_freq_order, english_freq_order)}
voy_to_lat = {v: l for v, l in zip(voynich_freq_order, latin_freq_order)}

sample_words = all_words[:30]
eng_decoded = apply_substitution(sample_words, voy_to_eng)
lat_decoded = apply_substitution(sample_words, voy_to_lat)

print("\n=== SAMPLE DECODING (simple frequency-rank substitution) ===")
print(f"{'Original':<12}{'-> \"English\" mapping':<20}{'-> \"Latin\" mapping':<20}")
for orig, eng, lat in zip(sample_words, eng_decoded, lat_decoded):
    print(f"{orig:<12}{eng:<20}{lat:<20}")
