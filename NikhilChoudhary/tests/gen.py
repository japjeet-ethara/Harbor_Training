import os
import random
import sys

# Ensure python-titlecase is importable
repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'python-titlecase'))
if not os.path.exists(repo_path):
    repo_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'environment', 'repo'))
sys.path.insert(0, repo_path)
from titlecase import titlecase

# Set random seed for 100% deterministic test data generation
random.seed(1)

# Word banks covering vocabulary and all 12 edge cases
SMALL_WORDS = [
    'a', 'an', 'and', 'as', 'at', 'but', 'by', 'en', 'for', 'if', 'in',
    'of', 'on', 'or', 'the', 'to', 'v', 'v.', 'via', 'vs', 'vs.'
]

HONORIFICS = ['mr', 'mrs', 'ms', 'dr', 'Mr', 'Mrs', 'Ms', 'Dr']

ACRONYMS = [
    'cnn', 'bbc', 'fbi', 'html', 'xml', 'http', 'css', 'sql', 'sdk',
    'tcp', 'udp', 'dns', 'png', 'jpg', 'pdf', 'rpm', 'cpu', 'gpu',
    'ssh', 'ssl', 'tls', 'ntp', 'ftp', 'bgp', 'cli'
]

URLS_AND_DOMAINS = [
    'example.com', 'del.icio.us', 'google.com', 'nytimes.com', 'amazon.co.uk',
    'github.com', 'sub.domain.org', 'index.html', 'script.min.js', 'data.tar.gz',
    'api.service.io', 'test.co.jp', 'docs.python.org', 'golang.org/x/tools'
]

CAMEL_CASE = [
    'iTunes', 'AT&T', 'eBay', 'iPhone', 'macOS', 'OpenAI', 'ChatGPT',
    'PostgreSQL', 'JavaScript', 'TypeScript', 'GitHub', 'YouTube',
    'FastAPI', 'BigQuery', 'microSD', 'QuickTime', 'FedEx', 'NextGen'
]

COMPOUNDS = [
    'state-of-the-art', 'end-to-end', 'face-to-face', 'up-to-date',
    'one-on-one', 'and/or', 'tcp/ip', 'input/output', 'read/write',
    'client/server', 'pass/fail', 'a-b', 'two-not-three/three-by-four/five-and',
    'in-and-out', 'more-or-less', 'back-to-back', 'day-to-day', 'step-by-step'
]

MC_MAC = [
    'mctavish', 'macdonalds', 'mcdonald', 'macarthur', 'macintosh',
    'mcgregor', 'macgregor', 'mckinley', 'macleod', 'mcmahon',
    'mcfarland', 'macpherson', 'mcclure', 'mccarthy'
]

APOSTROPHE_NAMES = [
    "o'reilly", "o'connor", "o'doyle", "o'brien", "l'grange",
    "d'angelo", "o'grange", "o'grange's", "o'dell", "o'neill",
    "l'enfant", "d'artagnan"
]

DOTTED_INITIALS = ['D.C.', 'U.S.A.', 'U.K.', 'N.Y.C.', 'P.R.C.', 'E.U.']

REGULAR_NOUNS = [
    'guide', 'report', 'handbook', 'analysis', 'system', 'network',
    'architecture', 'overview', 'chronicles', 'adventures', 'journey',
    'investigation', 'future', 'history', 'evolution', 'foundation',
    'whisper', 'shadow', 'echo', 'legend', 'mystery', 'paradox',
    'protocol', 'algorithm', 'discovery', 'odyssey', 'manifesto'
]

REGULAR_ADJECTIVES = [
    'complete', 'essential', 'ultimate', 'modern', 'ancient', 'secret',
    'hidden', 'practical', 'comprehensive', 'advanced', 'simple',
    'brilliant', 'silent', 'golden', 'digital', 'quantum', 'global',
    'dynamic', 'stellar', 'crucial', 'definitive', 'infinite'
]

REGULAR_VERBS = [
    'building', 'understanding', 'designing', 'exploring', 'mastering',
    'discovering', 'creating', 'transforming', 'learning', 'unleashing',
    'optimizing', 'scaling', 'refactoring', 'decoding', 'navigating'
]

SUBPHRASE_DELIMITERS = [': ', '; ', ' - ', ' — ', ' – ', '. ']

def generate_single_title(idx):
    category = idx % 12
    # Ensure wide variety of lengths and structures
    adj = random.choice(REGULAR_ADJECTIVES)
    noun1 = random.choice(REGULAR_NOUNS)
    noun2 = random.choice(REGULAR_NOUNS)
    verb = random.choice(REGULAR_VERBS)
    sm = random.choice(SMALL_WORDS)
    
    if category == 0:
        # 1. Small words internal
        title = f"{verb} {sm} {adj} {noun1} {random.choice(SMALL_WORDS)} {noun2}"
    elif category == 1:
        # 2. First and last words small or quoted
        flavor = idx % 4
        if flavor == 0:
            title = f"{sm} {noun1} {random.choice(SMALL_WORDS)} {adj} {noun2} {random.choice(['of', 'for', 'in', 'to', 'on'])}"
        elif flavor == 1:
            title = f"'{sm} {adj} {noun1} {random.choice(['of', 'at', 'by'])}'"
        elif flavor == 2:
            title = f'"{sm} {noun1} is nothing to be afraid of"'
        else:
            title = f"why {noun1} is what we look for"
    elif category == 2:
        # 3. Sub-phrase boundaries
        delim = random.choice(SUBPHRASE_DELIMITERS)
        title = f"{adj} {noun1}{delim}{random.choice(SMALL_WORDS)} {adj} {noun2}"
    elif category == 3:
        # 4. All-caps line
        flavor = idx % 3
        if flavor == 0:
            title = f"THE {adj.upper()} {noun1.upper()} AND THE {noun2.upper()}"
        elif flavor == 1:
            title = f"EPISODE {idx % 20}: THE {noun1.upper()} OF {noun2.upper()}"
        else:
            title = f"{verb.upper()} {noun1.upper()} IN {random.choice(DOTTED_INITIALS)} TODAY"
    elif category == 4:
        # 5. Acronyms (consonant-only)
        acronym = random.choice(ACRONYMS)
        title = f"{verb} {acronym} for {adj} {noun1} and {random.choice(ACRONYMS)}"
    elif category == 5:
        # 6. Inline periods (domains / filenames)
        url = random.choice(URLS_AND_DOMAINS)
        title = f"visiting {url} to download {random.choice(URLS_AND_DOMAINS)} securely"
    elif category == 6:
        # 7. Mixed-case / CamelCase
        cc = random.choice(CAMEL_CASE)
        title = f"developing with {cc} and {random.choice(CAMEL_CASE)} on {random.choice(CAMEL_CASE)}"
    elif category == 7:
        # 8. Hyphenated and slash compounds
        comp = random.choice(COMPOUNDS)
        title = f"{comp} architecture for {random.choice(COMPOUNDS)} systems"
    elif category == 8:
        # 9. Mc / Mac prefixes
        mc = random.choice(MC_MAC)
        title = f"how {mc} and {random.choice(MC_MAC)} built the {adj} {noun1}"
    elif category == 9:
        # 10. Apostrophe prefixes
        ap = random.choice(APOSTROPHE_NAMES)
        title = f"{ap} meets {random.choice(APOSTROPHE_NAMES)} at the {noun1}"
    elif category == 10:
        # 11. Honorifics
        h = random.choice(HONORIFICS)
        title = f"{h} {random.choice(MC_MAC)} and {random.choice(HONORIFICS)} {random.choice(APOSTROPHE_NAMES)} on {noun1}"
    else:
        # 12. Dotted initials & complex combinations
        init = random.choice(DOTTED_INITIALS)
        title = f"{adj} {noun1} in {init}: from {random.choice(ACRONYMS)} to {random.choice(CAMEL_CASE)}"

    # Add index uniqueness suffix to guarantee 100% distinct titles
    # But integrate it naturally as volume/edition/part or serial tag
    mod = idx % 5
    if mod == 0:
        title = f"{title} (vol. {idx + 1})"
    elif mod == 1:
        title = f"{title} - part {idx + 1}"
    elif mod == 2:
        title = f"{title}: edition {idx + 1}"
    elif mod == 3:
        title = f"{title} #{idx + 1}"
    else:
        title = f"{title} [{idx + 1}]"

    # Ensure no internal line breaks or trailing whitespace
    title = title.replace('\r', ' ').replace('\n', ' ').strip()
    return title

def generate_pool(count, offset=0):
    titles = []
    seen = set()
    idx = offset
    while len(titles) < count:
        t = generate_single_title(idx)
        idx += 1
        if t not in seen:
            seen.add(t)
            titles.append(t)
    return titles

def main():
    data_dir = os.path.join(os.path.dirname(__file__), 'data')
    os.makedirs(data_dir, exist_ok=True)

    print("Generating 2,000 public inputs...")
    public_inputs = generate_pool(2000, offset=0)

    print("Generating 2,000 hidden inputs (non-overlapping)...")
    hidden_inputs = generate_pool(2000, offset=50000)

    # Ensure no overlap
    overlap = set(public_inputs).intersection(set(hidden_inputs))
    assert len(overlap) == 0, f"Error: found {len(overlap)} overlapping titles!"

    print("Computing expected outputs via python-titlecase...")
    public_expected = [titlecase(t) for t in public_inputs]
    hidden_expected = [titlecase(t) for t in hidden_inputs]

    # Write files
    inputs_path = os.path.join(data_dir, 'inputs.txt')
    expected_path = os.path.join(data_dir, 'expected.txt')
    hidden_inputs_path = os.path.join(data_dir, 'hidden_inputs.txt')
    hidden_expected_path = os.path.join(data_dir, 'hidden_expected.txt')

    with open(inputs_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(public_inputs) + '\n')

    with open(expected_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(public_expected) + '\n')

    with open(hidden_inputs_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(hidden_inputs) + '\n')

    with open(hidden_expected_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(hidden_expected) + '\n')

    print("Validating generated files...")
    for path, name in [
        (inputs_path, 'inputs.txt'),
        (expected_path, 'expected.txt'),
        (hidden_inputs_path, 'hidden_inputs.txt'),
        (hidden_expected_path, 'hidden_expected.txt')
    ]:
        assert os.path.exists(path), f"File {name} does not exist!"
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()
        assert len(lines) == 2000, f"File {name} has {len(lines)} lines, expected 2000!"
        for l in lines:
            assert '\n' not in l and '\r' not in l, f"Line break inside title in {name}!"

    print("All 4 test data files successfully generated and validated (2,000 lines each)!")

if __name__ == '__main__':
    main()
