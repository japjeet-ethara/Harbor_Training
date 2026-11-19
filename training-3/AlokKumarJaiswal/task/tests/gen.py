# -*- coding: utf-8 -*-
"""Generate dev and hidden titlecase fixtures from the original Python library.

Run with the active Python 3.12 interpreter (the project .venv). Expected lines
are whatever titlecase() returns; nothing in the output files is hand-written.
"""

import hashlib
import random
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parent.parent / "environment" / "repo"
sys.path.insert(0, str(REPO))

import titlecase as titlecase_mod  # noqa: E402

_mod_file = Path(titlecase_mod.__file__).resolve()
assert _mod_file.is_relative_to(REPO.resolve()), (
    f"{titlecase_mod.__file__} is not inside {REPO}"
)
print(titlecase_mod.__file__)

titlecase = titlecase_mod.titlecase

assert titlecase("my name is o'reilly") == "My Name Is O'Reilly"
assert titlecase("THIS IS ALL CAPS AND SHOULD BE ADDRESSED") == (
    "This Is All Caps and Should Be Addressed"
)
assert titlecase("mr") == "Mr"
assert titlecase("") == ""
assert titlecase("iTunes should be unmolested") == "iTunes Should Be Unmolested"


DATA_DIR = Path(__file__).resolve().parent / "data"
LINE_COUNT = 2000

# Printable ASCII, tab, and the six extra punctuation characters the task allows.
ALLOWED = set(map(chr, range(32, 127)))
ALLOWED.update("\t\u2018\u2019\u201c\u201d\u2013\u2014")

APOS_CHARS = ("'", "\u2018", "\u2019")  # ' ‘ ’
EN_DASH = "\u2013"
EM_DASH = "\u2014"
SUB_PUNCTS = (":", ".", ";", "?", "!", "-", EN_DASH, EM_DASH)
SUB_PUNCT_CHARS = set(SUB_PUNCTS)

SMALL_WORDS = (
    "a",
    "an",
    "and",
    "as",
    "at",
    "but",
    "by",
    "en",
    "for",
    "if",
    "in",
    "of",
    "on",
    "or",
    "the",
    "to",
    "v",
    "v.",
    "via",
    "vs",
    "vs.",
)
SMALL_SET = set(SMALL_WORDS)

# Ordinary words: lowercase ASCII, not small words. Hand-written.
CONTENT = (
    "apple", "bridge", "castle", "doctor", "engine", "forest", "garden",
    "harbor", "island", "journal", "kitchen", "letter", "market", "number",
    "orange", "paper", "quartz", "river", "silver", "tower", "uncle",
    "valley", "window", "zebra", "people", "public", "local", "large",
    "small", "social", "national", "special", "major", "clear", "recent",
    "strong", "human", "music", "science", "school", "office", "moment",
    "reason", "result", "change", "morning", "teacher", "student", "group",
    "problem", "question", "business", "service", "friend", "power",
    "minute", "parent", "health", "research", "force", "water", "house",
    "night", "point", "world", "child", "woman", "month", "right", "level",
    "north", "south", "light", "green", "black", "white", "simple",
    "famous", "common", "final", "open", "full", "free", "true", "real",
    "main", "high", "long", "great", "other", "new", "old", "good",
    "first", "last", "next", "same", "few", "many", "such", "even",
    "still", "back", "hand", "part", "place", "case", "week", "work",
    "life", "day", "man", "job", "book", "car", "team", "idea", "body",
    "face", "door", "art", "war", "air", "girl", "name", "line", "end",
    "law", "game", "head", "side", "kind", "room", "area", "fact", "lot",
    "hour", "kid", "home", "table", "chair", "plant", "stone", "cloud",
    "field", "coast", "train", "plane", "ship", "road", "park", "bank",
    "farm", "mine", "mill", "port", "camp", "lake", "hill", "path",
    "gate", "wall", "roof", "floor", "glass", "metal", "cloth", "bread",
    "sugar", "salt", "pepper", "coffee", "dinner", "lunch", "winter",
    "summer", "autumn", "spring", "monday", "report", "meeting", "budget",
    "design", "method", "figure", "sample", "record", "model", "signal",
    "camera", "button", "screen", "keyboard", "mouse", "cable", "motor",
    "piston", "valve", "brake", "wheel", "frame", "panel",
    "john", "mary", "robert", "susan", "david", "laura", "james", "karen",
    "michael", "linda", "william", "sarah", "richard", "thomas", "anna",
    "charles", "joseph", "grace", "george", "clara", "edward", "helen",
    "frank", "peter", "jane", "paul", "ruth", "mark", "andrew", "nora",
    "steven", "kevin", "alice", "iris",
)

VOWELS = set("aeiouy")

# Hand-written feature lists. Each is checked below so a typo cannot slip in.
O_NAMES = (
    "reilly", "brien", "connor", "neil", "malley", "hara", "donnell",
    "keefe", "shea", "rourke", "brian", "tool", "grady", "leary",
)
D_NAMES = ("angelo", "artagnan", "amico", "agostino", "alessandro", "andrea", "urso")
L_NAMES = ("amour", "oreal", "escalier", "oiseau", "heure", "etoile", "orange")
MC_NAMES = (
    "donald", "clelland", "intyre", "gregor", "tavish", "carthy", "mahon",
    "kinley", "connell", "dowell", "pherson", "bride", "neil", "leod",
    "queen", "allister", "intosh",
)
INTERNAL_CAPS = (
    "iTunes", "iPhone", "iPad", "eBay", "macOS", "blackBerry", "fedEx",
    "powerPoint", "wordPress", "javaScript", "youTube", "linkedIn",
    "gitHub", "mySQL", "openAI", "macBook", "eTrade", "iMac",
)
CONSONANT_WORDS = (
    "cnn", "tcp", "gps", "lcd", "ftp", "ssh", "nfl", "css", "rss",
    "mtv", "pdf", "dvd", "bbc", "cbs", "nbc", "pbs", "cdc", "npr",
    "tnt", "dhs", "pgp", "rpm", "sql", "jwt", "html", "xml", "ssd", "hdd",
    "mph", "tsv", "ctl", "cfg", "ptr",
    "nft", "dmv", "ghz", "mhz",
)
Y_WORDS = (
    "yellow", "sky", "happy", "style", "year", "young", "rhythm", "myth",
    "system", "pretty", "ready", "every", "story", "family", "history",
    "party", "country", "city", "sync", "byte", "type", "cycle",
)
VOWEL_WORDS = ("eye", "you", "aye", "iou", "eau", "yay", "yoyo", "oui", "ai", "oy", "ye")
HONORIFICS = ("mr", "mrs", "ms", "dr")
ORDINALS = ("34th", "3rd", "2nd", "21st", "1st", "100th", "22nd", "45th", "5th", "11th")
MONEY = ("$100", "$9.99", "$1", "$2500", "$0.50", "$42", "$1000")

# Hand-written sentence templates. Slots: c0..c5 content, s0..s5 small words.
TEMPLATES = (
    "{s0} {c0} {s1} {c1} {s2}",
    "{c0} {s0} {c1} {s1} {c2} {s2}",
    "{s0} {c0} {c1} {s1} {c2}",
    "{c0}: {s0} {c1} {s1} {c2}",
    "{c0}. {s0} {c1} {s1} {c2}",
    "{c0}; {s0} {c1} {s1} {c2}",
    "{c0}? {s0} {c1} {s1} {c2}",
    "{c0}! {s0} {c1} {s1} {c2}",
    "{c0} - {s0} {c1} {s1} {c2}",
    "{c0} {en} {s0} {c1} {s1} {c2}",
    "{c0} {em} {s0} {c1} {s1} {c2}",
    "{s0} {c0} {s1} {c1}: {s2} {c2}",
    "{s0} {c0}. {s1} {c1}; {s2} {c2}",
    "{c0} {c1} {s0} {c2} {s1} {c3} {s2}",
    "{s0} {s1} {c0} {s2} {c1} {c2}",
    "notes {s0} {c0}: {s1} {c1}. {s2} {c2}",
    "{c0} {s0} {c1} - {s1} {c2} {em} {s2} {c3}",
    "{s0} {c0}? {s1} {c1}! {s2} {c2}",
    "{c0}; {s0} {c1}: {s1} {c2}. {s2} {c3}",
    "{s0} {c0} {s1} {c1} {s2} {c2} {s3} {c3}",
    "{c0} {c1} {s0} {c2}. {s1} {c3}",
    "from {s0} {c0} {s1} {c1} {s2} {c2}",
    "{s0} {c0} {s1} the {c1} {s2} {c2}",
    "{c0}, {c1} {s0} {c2} {s1} {c3}",
    "{s0} {c0} and {c1} {s1} {c2} {s2}",
)

F_KINDS = (
    "and/or",
    "slash",
    "multi_slash",
    "end-to-end",
    "hyphen_multi",
    "lead_hyphen",
    "trail_hyphen",
    "en_glued",
    "em_glued",
    "en_spaced",
    "em_spaced",
)
G_KINDS = ("internal", "consonant", "y", "vowel")
H_KINDS = (
    "ordinal",
    "money",
    "paren",
    "dquote",
    "curly_quote",
    "bracket",
    "ellipsis",
    "amp",
    "hash",
    "mention",
)
C_KINDS = ("o", "O", "d", "l", "mc", "possessive", "o_poss")
D_KINDS = ("domain", "multi_domain", "dc", "eg", "ab", "initials")
E_KINDS = ("http", "https", "www", "email")
I_STYLES = ("leading", "trailing", "both", "multi", "tabs", "mixed")
J_CASES = ("lower", "upper", "title", "mixed")
J_POSITIONS = ("start", "middle", "end")
CATS = ("a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k")

WS_FORCED = (
    " ",
    "  ",
    "   ",
    "\t",
    "\t\t",
    " \t",
    "\t ",
    "  \t  ",
    "\t \t ",
    "   \t",
    "\t\t ",
    " \t ",
)


def _letters(word):
    return [ch for ch in word.lower() if ch.isalpha()]


def _check_word_lists():
    vowels = VOWELS
    assert all(w.lower() == w and w.isalpha() and w not in SMALL_SET for w in CONTENT)
    assert all(len(_letters(w)) >= 3 and all(ch not in vowels for ch in _letters(w)) for w in CONSONANT_WORDS)
    assert all("y" in w and w.isalpha() for w in Y_WORDS)
    assert all(_letters(w) and all(ch in vowels for ch in _letters(w)) for w in VOWEL_WORDS)
    assert all(any(ch.isupper() for ch in w[1:]) and any(ch.islower() for ch in w) for w in INTERNAL_CAPS)
    for group in (O_NAMES, D_NAMES, L_NAMES, MC_NAMES, CONTENT, Y_WORDS, VOWEL_WORDS, CONSONANT_WORDS):
        for word in group:
            assert all(ch in ALLOWED for ch in word), word
    for word in INTERNAL_CAPS:
        assert all(ch in ALLOWED for ch in word), word


_check_word_lists()


def chars_ok(line):
    return all(ch in ALLOWED for ch in line) and "\r" not in line and "\n" not in line


def mutate_case(rng, word, style=None):
    """Random case: lower, UPPER, Title, or mixed. Non-letters stay put."""
    if style is None:
        style = rng.choice(("lower", "upper", "title", "mixed"))
    if style == "lower":
        return word.lower()
    if style == "upper":
        return word.upper()
    if style == "title":
        chars = list(word)
        seen = False
        for i, ch in enumerate(chars):
            if ch.isalpha():
                chars[i] = ch.lower() if seen else ch.upper()
                seen = True
        return "".join(chars)
    idxs = [i for i, ch in enumerate(word) if ch.isalpha()]
    chars = list(word)
    if len(idxs) >= 2:
        bits = [rng.random() < 0.5 for _ in idxs]
        if all(bits) or not any(bits):
            bits[0] = True
            bits[1] = False
        for i, bit in zip(idxs, bits):
            chars[i] = chars[i].upper() if bit else chars[i].lower()
        return "".join(chars)
    return word.upper() if rng.random() < 0.5 else word.lower()


def attach_punct(rng, word):
    """Attach ASCII or allowed curly punctuation without adding whitespace."""
    roll = rng.random()
    if roll < 0.12:
        return word + rng.choice((",", ".", "?", "!", "..."))
    if roll < 0.20:
        pair = rng.choice(
            (
                ('"', '"'),
                ("'", "'"),
                ("(", ")"),
                ("[", "]"),
                ("\u201c", "\u201d"),
                ("\u2018", "\u2019"),
            )
        )
        return pair[0] + word + pair[1]
    if roll < 0.26:
        return rng.choice(("$", "#", "@")) + word
    return word


class Factory:
    """Build one input line for a requested set of category tags."""

    def __init__(self, rng, emit_empty):
        self.rng = rng
        self.emit_empty = emit_empty
        self.single_made = 0
        self.long_made = 0
        self.full_made = 0
        self.partial_made = 0
        self.ws_only_made = 0
        self.decor_made = 0
        self.cursors = {
            "small_start": 0,
            "small_middle": 0,
            "small_end": 0,
            "small_after": 0,
            "punct": 0,
            "template": 0,
            "f": 0,
            "g": 0,
            "h": 0,
            "c": 0,
            "d": 0,
            "dc": 0,
            "eg": 0,
            "ab": 0,
            "e": 0,
            "apos": 0,
            "mc": 0,
            "j_word": 0,
            "j_pos": 0,
            "i_style": 0,
        }

    def _next(self, key, seq):
        i = self.cursors[key]
        self.cursors[key] = i + 1
        return seq[i % len(seq)]

    def _content(self):
        return self.rng.choice(CONTENT)

    def _small(self, slot):
        return self._next("small_" + slot, SMALL_WORDS)

    def fill_template(self):
        tpl = self._next("template", TEMPLATES)
        data = {f"c{i}": self._content() for i in range(6)}
        data.update({f"s{i}": self.rng.choice(SMALL_WORDS) for i in range(6)})
        data["en"] = EN_DASH
        data["em"] = EM_DASH
        return tpl.format(**data)

    def _cycle_token(self, key, kinds, builder):
        kind = self._next(key, kinds)
        return kind, builder(kind)

    def c_token(self):
        kind = self._next("c", C_KINDS)
        apos = APOS_CHARS[self.cursors["apos"] % len(APOS_CHARS)]
        self.cursors["apos"] += 1
        if kind == "o":
            token = "o" + apos + self.rng.choice(O_NAMES)
        elif kind == "O":
            token = "O" + apos + self.rng.choice(O_NAMES)
        elif kind == "d":
            token = "d" + apos + self.rng.choice(D_NAMES)
        elif kind == "l":
            token = "l" + apos + self.rng.choice(L_NAMES)
        elif kind == "mc":
            prefix = ("mc", "Mc", "MC")[self.cursors["mc"] % 3]
            self.cursors["mc"] += 1
            token = prefix + self.rng.choice(MC_NAMES)
        elif kind == "possessive":
            token = self._content() + apos + "s"
        else:
            token = "o" + apos + self.rng.choice(O_NAMES) + apos + "s"
        return token

    def d_token(self):
        kind = self._next("d", D_KINDS)
        if kind == "domain":
            return self._content() + self.rng.choice((".com", ".org", ".net", ".edu"))
        if kind == "multi_domain":
            host = self.rng.choice(("news", "mail", "cdn", "docs"))
            return host + "." + self._content() + self.rng.choice((".com", ".org"))
        if kind == "dc":
            return self._next("dc", ("D.C.", "d.c.", "U.S.", "U.S.A.", "u.s."))
        if kind == "eg":
            return self._next("eg", ("e.g.", "i.e.", "E.G.", "a.m.", "p.m."))
        if kind == "ab":
            return self._next("ab", ("a.b", "x.y", "Ph.D", "Ph.D."))
        letters = [
            self.rng.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
            for _ in range(self.rng.randint(2, 4))
        ]
        token = ".".join(letters)
        if self.rng.random() < 0.5:
            token += "."
        return token

    def e_token(self):
        kind = self._next("e", E_KINDS)
        host = self._content() + self.rng.choice((".com", ".org", ".net"))
        parts = [self._content() for _ in range(self.rng.randint(1, 3))]
        path = "/" + "/".join(parts)
        if kind == "http":
            return "http://" + host + path
        if kind == "https":
            extra = ""
            if self.rng.random() < 0.5:
                extra = "?q=" + self._content()
            return "https://" + host + path + extra
        if kind == "www":
            return "www." + host + path
        user = self._content()
        if self.rng.random() < 0.5:
            user = user + "." + self._content()
        domain = self._content() + "." + self.rng.choice(("com", "org", "net"))
        return user + "@" + domain

    def f_token(self, spaced_ok):
        kind = self._next("f", F_KINDS)
        if not spaced_ok and kind in ("en_spaced", "em_spaced"):
            kind = "en_glued" if "en" in kind else "em_glued"
        if kind == "and/or":
            return "and/or", kind
        if kind == "slash":
            left = self.rng.choice(SMALL_WORDS + CONTENT)
            right = self.rng.choice(SMALL_WORDS + CONTENT)
            return left + "/" + right, kind
        if kind == "multi_slash":
            parts = [self.rng.choice(CONTENT) for _ in range(self.rng.randint(3, 4))]
            return "/".join(parts), kind
        if kind == "end-to-end":
            return "end-to-end", kind
        if kind == "hyphen_multi":
            if self.rng.random() < 0.5:
                parts = [self._content(), self.rng.choice(SMALL_WORDS), self._content()]
            else:
                parts = [self._content() for _ in range(self.rng.randint(3, 4))]
            return "-".join(parts), kind
        if kind == "lead_hyphen":
            return "-" + self._content(), kind
        if kind == "trail_hyphen":
            return self._content() + "-", kind
        if kind == "en_glued":
            return self._content() + EN_DASH + self._content(), kind
        if kind == "em_glued":
            return self._content() + EM_DASH + self._content(), kind
        if kind == "en_spaced":
            return EN_DASH, kind
        return EM_DASH, kind

    def g_token(self):
        kind = self._next("g", G_KINDS)
        if kind == "internal":
            return self.rng.choice(INTERNAL_CAPS)
        if kind == "consonant":
            return self.rng.choice(CONSONANT_WORDS)
        if kind == "y":
            return self.rng.choice(Y_WORDS)
        return self.rng.choice(VOWEL_WORDS)

    def h_token(self):
        kind = self._next("h", H_KINDS)
        word = self._content()
        if kind == "ordinal":
            return self.rng.choice(ORDINALS)
        if kind == "money":
            return self.rng.choice(MONEY)
        if kind == "paren":
            return "(" + word + ")"
        if kind == "dquote":
            return '"' + word + '"'
        if kind == "curly_quote":
            return "\u201c" + word + "\u201d"
        if kind == "bracket":
            return "[" + word + "]"
        if kind == "ellipsis":
            if self.rng.random() < 0.5:
                return "..."
            return word + "..."
        if kind == "amp":
            return self.rng.choice(("&", "AT&T", "Q&A", "R&D"))
        if kind == "hash":
            return "#" + word
        return "@" + word

    def j_token(self):
        base, style = self._next("j_word", tuple((b, s) for b in HONORIFICS for s in J_CASES))
        if style == "lower":
            token = base
        elif style == "upper":
            token = base.upper()
        elif style == "title":
            token = base.capitalize()
        else:
            chars = list(base)
            chars[0] = chars[0].lower()
            chars[-1] = chars[-1].upper()
            for i in range(1, len(chars) - 1):
                chars[i] = chars[i].upper() if self.rng.random() < 0.5 else chars[i].lower()
            token = "".join(chars)
        pos = self._next("j_pos", J_POSITIONS)
        return token, pos

    def make_ws(self, index, salt):
        if index < len(WS_FORCED) and not salt:
            core = WS_FORCED[index]
        else:
            n = self.rng.randint(2, 18)
            core = "".join(self.rng.choice((" ", "\t")) for _ in range(n))
            if "\t" not in core:
                core = "\t" + core
            if "  " not in core:
                core = core + "  "
        tail_n = self.rng.randint(1, 30)
        if salt:
            tail_n += self.rng.randint(5, 15)
        return core + (" " * tail_n)

    def pick_mode(self, cats):
        catset = set(cats)
        if catset == {"i"}:
            if self.ws_only_made < 10:
                return "ws"
            if self.decor_made < 10:
                return "short"
            return "ws" if self.rng.random() < 0.45 else "short"
        if "k" in catset:
            others = [c for c in CATS if c in catset and c not in ("k", "i")]
            if catset == {"k"}:
                if self.single_made < 24:
                    return "single"
                if self.long_made < 24:
                    return "long"
                return "single" if self.rng.random() < 0.35 else "long"
            needs_words = "a" in catset or "i" in catset or len(others) >= 2
            one = others[0] if len(others) == 1 else None
            # Honorifics have only a handful of spellings; keep them inside sentences.
            can_single = (not needs_words) and one != "j"
            if can_single and self.rng.random() < 0.22:
                return "single"
            return "long"
        return "short"

    def single_line(self, cats):
        others = [c for c in CATS if c in cats and c != "k"]
        other = others[0] if others else None
        if other is None:
            return mutate_case(self.rng, self._content())
        if other == "b":
            return self._content().upper()
        if other == "c":
            return self.c_token()
        if other == "d":
            return self.d_token()
        if other == "e":
            return self.e_token()
        if other == "f":
            token, _kind = self.f_token(spaced_ok=False)
            return token
        if other == "g":
            return self.g_token()
        if other == "h":
            return self.h_token()
        return mutate_case(self.rng, self._content())

    def _insert(self, items, token):
        if len(items) < 2:
            items.append((token, True))
            return
        idx = 1 + self.rng.randrange(len(items) - 1)
        items.insert(idx, (token, True))

    def _apply_a(self, items):
        while len(items) < 7:
            at = max(1, len(items) // 2)
            items.insert(at, (self._content(), False))
        s_start = self._small("start")
        s_mid = self._small("middle")
        s_end = self._small("end")
        s_after = self._small("after")
        punct = self._next("punct", SUB_PUNCTS)

        if items[0][1] and items[0][0].lower() not in SMALL_SET:
            items.insert(0, (s_start, True))
        else:
            items[0] = (s_start, True)
        if items[-1][1] and items[-1][0].lower() not in SMALL_SET:
            items.append((s_end, True))
        else:
            items[-1] = (s_end, True)

        mid = len(items) // 2
        if mid in (0, len(items) - 1):
            mid = 1 if len(items) > 2 else 0
        if items[mid][1] and items[mid][0].lower() not in SMALL_SET:
            items.insert(mid, (s_mid, True))
        else:
            items[mid] = (s_mid, True)

        banned = {0, len(items) - 1, mid}
        plain = [
            i
            for i, (word, locked) in enumerate(items)
            if not locked and i not in banned and i + 1 < len(items)
        ]
        if plain:
            idx = self.rng.choice(plain)
            base = items[idx][0]
            if (not base.isalpha()) or base.lower() in SMALL_SET:
                base = self._content()
            items[idx] = (base + punct, True)
            nxt = idx + 1
            if items[nxt][1] and items[nxt][0].lower() not in SMALL_SET:
                items.insert(nxt, (s_after, True))
            else:
                items[nxt] = (s_after, True)
        else:
            at = max(1, len(items) - 1)
            items.insert(at, (self._content() + punct, True))
            items.insert(at + 1, (s_after, True))

    def _place_honorific(self, items, token, pos, cats):
        if "a" in cats and pos in ("start", "end"):
            pos = "middle"
        if pos == "start":
            items.insert(0, (token, True))
        elif pos == "end":
            items.append((token, True))
        else:
            mid = len(items) // 2
            items.insert(mid, (token, True))

    def _fit(self, items, lo, hi):
        guard = 0
        while len(items) < lo and guard < 100:
            at = max(1, len(items) // 2) if items else 0
            items.insert(at, (self._content(), False))
            guard += 1
        guard = 0
        while len(items) > hi and guard < 100:
            unlocked = [i for i, (_w, locked) in enumerate(items) if not locked]
            if not unlocked:
                break
            del items[unlocked[-1]]
            guard += 1

    def _case_items(self, items, cats, caps):
        if caps == "full":
            return [(word.upper(), locked) for word, locked in items]
        if caps == "partial":
            lowered = []
            cands = []
            for word, locked in items:
                if locked:
                    lowered.append((word, True))
                else:
                    lowered.append((word.lower(), False))
                    letters = [ch for ch in word if ch.isalpha()]
                    if len(letters) >= 2:
                        cands.append(len(lowered) - 1)
            if len(cands) < 2:
                lowered.append((self._content().upper(), True))
                lowered.append((self._content().upper(), True))
                return lowered
            for idx in self.rng.sample(cands, 2):
                lowered[idx] = (lowered[idx][0].upper(), True)
            return lowered
        if "a" in cats:
            return items
        out = []
        for word, locked in items:
            if locked:
                out.append((word, True))
            else:
                out.append((mutate_case(self.rng, word), False))
        return out

    def _apply_ws(self, line, preserve_sub):
        style = self._next("i_style", I_STYLES)

        def rewrite_spaces(maker):
            out = []
            for i, ch in enumerate(line):
                if ch != " ":
                    out.append(ch)
                    continue
                prev = line[i - 1] if i else ""
                if preserve_sub and prev in SUB_PUNCT_CHARS:
                    out.append(" ")
                else:
                    out.append(maker())
            return "".join(out)

        if style == "leading":
            return " " * self.rng.randint(1, 5) + line
        if style == "trailing":
            return line + " " * self.rng.randint(1, 5)
        if style == "both":
            return (" " * self.rng.randint(1, 3)) + line + " \t"
        if style == "multi":
            return rewrite_spaces(lambda: " " * self.rng.randint(2, 4))
        if style == "tabs":
            return rewrite_spaces(lambda: "\t")
        mixed = rewrite_spaces(
            lambda: self.rng.choice(("  ", "   ", "\t", "\t\t", " \t "))
        )
        return "\t" + mixed + " "

    def compose(self, cats, salt=False):
        catset = set(cats)
        if self.emit_empty and catset == {"i"} and not salt:
            return "", {"kind": "ws", "caps": None, "i_style": "ws"}

        mode = self.pick_mode(cats)
        if mode == "ws":
            line = self.make_ws(self.ws_only_made, salt)
            if not line:
                line = " "
            return line, {"kind": "ws", "caps": None, "i_style": "ws"}

        if mode == "single":
            line = self.single_line(cats)
            if salt:
                line = line + str(self.rng.randrange(1_000_000))
            if any(ch.isspace() for ch in line) or not chars_ok(line) or not line:
                raise RuntimeError(f"bad single token {line!r}")
            caps = "full" if line.isupper() and any(ch.isalpha() for ch in line) else None
            return line, {"kind": "single", "caps": caps, "i_style": None}

        feature_n = sum(c in catset for c in ("c", "d", "e", "f", "g", "h", "j"))
        if mode == "long":
            slack = feature_n + (4 if "a" in catset else 0)
            hi_base = max(30, 56 - slack)
            lo_base = min(34, hi_base)
            base_n = self.rng.randint(lo_base, hi_base)
        else:
            base_n = self.rng.randint(6, 12)

        if "a" in catset and self.rng.random() < 0.55:
            words = self.fill_template().split(" ")
            if len(words) > base_n:
                words = words[:base_n]
            while len(words) < base_n:
                words.append(self._content())
        else:
            words = [self._content() for _ in range(base_n)]
        items = [(word, False) for word in words]

        if "c" in catset:
            self._insert(items, self.c_token())
        if "d" in catset:
            self._insert(items, self.d_token())
        if "e" in catset:
            self._insert(items, self.e_token())
        if "f" in catset:
            token, _kind = self.f_token(spaced_ok=True)
            self._insert(items, token)
        if "g" in catset:
            self._insert(items, self.g_token())
        if "h" in catset:
            self._insert(items, self.h_token())

        if mode == "long":
            self._fit(items, 30, 52)
        if "a" in catset:
            self._apply_a(items)

        if "j" in catset:
            token, pos = self.j_token()
            self._place_honorific(items, token, pos, catset)

        special = any(c in catset for c in ("c", "d", "e", "f", "g", "h", "j"))
        caps = None
        if "b" in catset:
            if not special and self.full_made < 22:
                caps = "full"
            elif not special and self.partial_made < 22:
                caps = "partial"
            elif not special and self.rng.random() < 0.4:
                caps = "full"
            else:
                caps = "partial"

        # Punctuation sticks to ordinary words before case is assigned.
        punched = []
        for word, locked in items:
            if (not locked) and "a" not in catset and caps != "full":
                word = attach_punct(self.rng, word)
            punched.append((word, locked))
        items = punched

        if salt:
            unlocked = [i for i, (_w, locked) in enumerate(items) if not locked]
            extra = self._content() + str(self.rng.randrange(1_000_000))
            if unlocked:
                items[unlocked[-1]] = (extra, False)
            else:
                items.append((extra, False))

        items = self._case_items(items, catset, caps)
        if mode == "long":
            self._fit(items, 30, 60)
            if not (30 <= len(items) <= 60):
                raise RuntimeError(f"long line has {len(items)} words for {sorted(catset)}")
        elif len(items) < 4:
            self._fit(items, 4, 40)

        line = " ".join(word for word, _locked in items)
        i_style = None
        if "i" in catset:
            line = self._apply_ws(line, preserve_sub=("a" in catset and caps != "full"))
            i_style = "decor"
        if not chars_ok(line):
            bad = sorted({ch for ch in line if ch not in ALLOWED})
            raise RuntimeError(f"disallowed characters {bad!r} in {line!r}")
        if mode == "long" and not (30 <= len(line.split()) <= 60):
            raise RuntimeError(
                f"split count {len(line.split())} after spacing for {sorted(catset)}"
            )
        return line, {"kind": "long" if mode == "long" else "short", "caps": caps, "i_style": i_style}

    def observe(self, meta):
        kind = meta["kind"]
        if kind == "single":
            self.single_made += 1
        elif kind == "long":
            self.long_made += 1
        if meta.get("caps") == "full":
            self.full_made += 1
        elif meta.get("caps") == "partial":
            self.partial_made += 1
        if meta.get("i_style") == "ws":
            self.ws_only_made += 1
        elif meta.get("i_style") == "decor":
            self.decor_made += 1


def generate(rng, used, multi_target, emit_empty):
    factory = Factory(rng, emit_empty=emit_empty)
    lines = []
    tags = []
    counts = {cat: 0 for cat in CATS}
    multi = 0

    def try_add(requested):
        nonlocal multi
        cats = [cat for cat in CATS if cat in set(requested)]
        for attempt in range(40):
            line, meta = factory.compose(cats, salt=attempt >= 12)
            # "" may occur once per set, and once in the other set.
            if line == "":
                if line in lines or not chars_ok(line):
                    continue
            elif line in used or not chars_ok(line):
                continue
            if "\r" in line or "\n" in line:
                continue
            used.add(line)
            lines.append(line)
            tags.append(set(cats))
            for cat in cats:
                counts[cat] += 1
            if len(cats) >= 2:
                multi += 1
            if line == "":
                factory.emit_empty = False
            factory.observe(meta)
            return
        raise RuntimeError(f"could not build a unique line for {cats}")

    for cat in CATS:
        for _ in range(40):
            try_add([cat])

    while len(lines) < LINE_COUNT:
        if multi < multi_target:
            width = 2 if rng.random() < 0.7 else 3
            chosen = rng.sample(list(CATS), width)
        else:
            chosen = [rng.choice(CATS)]
        try_add(chosen)

    if len(lines) != LINE_COUNT:
        raise RuntimeError(f"expected {LINE_COUNT} lines, got {len(lines)}")
    return lines, tags, counts, multi


def expected_for(lines):
    out = []
    for line in lines:
        result = titlecase(line)
        if "\r" in result or "\n" in result:
            raise RuntimeError(f"titlecase introduced a break for {line!r} -> {result!r}")
        out.append(result)
    if len(out) != len(lines):
        raise RuntimeError("line count mismatch between input and expected")
    return out


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        for line in lines:
            handle.write(line)
            handle.write("\n")


def read_lines(path):
    with open(path, "r", encoding="utf-8", newline="\n") as handle:
        text = handle.read()
    if "\r" in text:
        raise RuntimeError(f"{path} contains CR")
    if not text.endswith("\n"):
        raise RuntimeError(f"{path} does not end with newline")
    parts = text.split("\n")
    if parts[-1] != "":
        raise RuntimeError(f"{path} has no final newline")
    return parts[:-1]


def sha256_file(path):
    with open(path, "r", encoding="utf-8", newline="\n") as handle:
        text = handle.read()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _word_letters_upper(word):
    letters = [ch for ch in word if ch.isalpha()]
    return len(letters) >= 2 and all(ch.isupper() for ch in letters)


def _honor_class(word):
    if word.islower():
        return "lower"
    if word.isupper():
        return "upper"
    if word[:1].isupper() and word[1:].islower():
        return "title"
    if any(ch.islower() for ch in word) and any(ch.isupper() for ch in word):
        return "mixed"
    return "other"


def assert_coverage(label, lines, tags):
    grouped = {cat: [] for cat in CATS}
    multi = 0
    for line, tag in zip(lines, tags):
        if len(tag) >= 2:
            multi += 1
        for cat in tag:
            grouped[cat].append(line)
    for cat in CATS:
        if len(grouped[cat]) < 40:
            raise RuntimeError(f"{label} category {cat} has {len(grouped[cat])} lines")

    a_lines = grouped["a"]
    blob_a = "\n".join(line.lower() for line in a_lines)
    for word in SMALL_WORDS:
        starts = 0
        middles = 0
        ends = 0
        after = 0
        for line in a_lines:
            parts = line.split()
            if not parts:
                continue
            if parts[0].lower() == word:
                starts += 1
            if parts[-1].lower() == word:
                ends += 1
            if any(part.lower() == word for part in parts[1:-1]):
                middles += 1
            for punct in SUB_PUNCTS:
                if (punct + " " + word) in line.lower():
                    after += 1
                    break
        if starts < 1 or middles < 1 or ends < 1 or after < 1:
            raise RuntimeError(
                f"{label} small word {word!r} positions "
                f"start={starts} middle={middles} end={ends} after={after}"
            )
    for punct in SUB_PUNCTS:
        if not any((punct + " " + word) in blob_a for word in SMALL_WORDS):
            raise RuntimeError(f"{label} missing subphrase punct {punct!r}")

    b_lines = grouped["b"]
    full = [
        line
        for line in b_lines
        if any(ch.isalpha() for ch in line) and line.upper() == line
    ]
    partial = []
    for line in b_lines:
        if line.upper() == line:
            continue
        if any(ch.islower() for ch in line) and any(
            _word_letters_upper(word) for word in line.split()
        ):
            partial.append(line)
    if not full or not partial:
        raise RuntimeError(f"{label} caps coverage full={len(full)} partial={len(partial)}")

    c_blob = "\n".join(grouped["c"])
    c_low = c_blob.lower()
    if not re.search(r"\bo['\u2018\u2019][a-z]", c_blob):
        raise RuntimeError(f"{label} missing o' names")
    if not re.search(r"\bO['\u2018\u2019]", c_blob):
        raise RuntimeError(f"{label} missing O' names")
    if not re.search(r"\bd['\u2018\u2019][a-z]", c_blob):
        raise RuntimeError(f"{label} missing d' names")
    if not re.search(r"\bl['\u2018\u2019][a-z]", c_blob):
        raise RuntimeError(f"{label} missing l' names")
    if not re.search(r"(?<![A-Za-z])mc[a-z]{2,}", c_blob):
        raise RuntimeError(f"{label} missing mc prefix")
    if not re.search(r"(?<![A-Za-z])Mc[A-Za-z]{2,}", c_blob):
        raise RuntimeError(f"{label} missing Mc prefix")
    if not re.search(r"(?<![A-Za-z])MC[A-Za-z]{2,}", c_blob):
        raise RuntimeError(f"{label} missing MC prefix")
    if not re.search(r"[A-Za-z]'s\b", c_blob) or not re.search(r"[A-Za-z]\u2019s\b", c_blob):
        raise RuntimeError(f"{label} missing possessives")
    for ch in APOS_CHARS:
        if ch not in c_blob:
            raise RuntimeError(f"{label} apostrophe {ch!r} missing from category c")
    if "o'" not in c_low and "o\u2018" not in c_low and "o\u2019" not in c_low:
        raise RuntimeError(f"{label} o-apostrophe missing")

    d_blob = "\n".join(grouped["d"])
    d_low = d_blob.lower()
    if not re.search(r"\b[a-z0-9-]+\.(com|org|net|edu)\b", d_low):
        raise RuntimeError(f"{label} missing dotted domain")
    if "d.c." not in d_low:
        raise RuntimeError(f"{label} missing D.C.")
    if "e.g." not in d_low:
        raise RuntimeError(f"{label} missing e.g.")
    if "a.b" not in d_blob:
        raise RuntimeError(f"{label} missing a.b")
    if not re.search(r"\b[A-Z](?:\.[A-Z])+\.?\b", d_blob):
        raise RuntimeError(f"{label} missing initials like A.B")

    e_lines = grouped["e"]
    if not any("http://" in line for line in e_lines):
        raise RuntimeError(f"{label} missing http://")
    if not any("https://" in line for line in e_lines):
        raise RuntimeError(f"{label} missing https://")
    if not any("www." in line.lower() and "/" in line for line in e_lines):
        raise RuntimeError(f"{label} missing www path")
    if not any(
        ("http://" in line or "https://" in line) and line.lower().count("/") >= 3
        for line in e_lines
    ):
        raise RuntimeError(f"{label} missing url path")
    if not any(re.search(r"[\w.]+@[\w.-]+\.[A-Za-z]{2,}", line) for line in e_lines):
        raise RuntimeError(f"{label} missing email-like token")

    f_lines = grouped["f"]
    f_low = "\n".join(line.lower() for line in f_lines)
    if "and/or" not in f_low:
        raise RuntimeError(f"{label} missing and/or")
    if "end-to-end" not in f_low:
        raise RuntimeError(f"{label} missing end-to-end")
    if not any(any(word.count("-") >= 2 for word in line.split()) for line in f_lines):
        raise RuntimeError(f"{label} missing multiple hyphens")
    if not any(
        any(word.startswith("-") and len(word) > 1 for word in line.split())
        for line in f_lines
    ):
        raise RuntimeError(f"{label} missing leading hyphen")
    if not any(
        any(word.endswith("-") and len(word) > 1 for word in line.split())
        for line in f_lines
    ):
        raise RuntimeError(f"{label} missing trailing hyphen")
    if not any(
        any(EN_DASH in word and word != EN_DASH for word in line.split()) for line in f_lines
    ):
        raise RuntimeError(f"{label} missing glued en dash")
    if not any(any(word == EN_DASH for word in line.split()) for line in f_lines):
        raise RuntimeError(f"{label} missing spaced en dash")
    if not any(
        any(EM_DASH in word and word != EM_DASH for word in line.split()) for line in f_lines
    ):
        raise RuntimeError(f"{label} missing glued em dash")
    if not any(any(word == EM_DASH for word in line.split()) for line in f_lines):
        raise RuntimeError(f"{label} missing spaced em dash")

    g_lines = grouped["g"]
    if not any(any(token in line for token in INTERNAL_CAPS) for line in g_lines):
        raise RuntimeError(f"{label} missing internal capitals")
    consonant_set = set(CONSONANT_WORDS)
    if not any(
        any(word.lower() in consonant_set for word in line.split()) for line in g_lines
    ):
        raise RuntimeError(f"{label} missing consonant-only words")
    y_set = set(Y_WORDS)
    if not any(any(word.lower() in y_set for word in line.split()) for line in g_lines):
        raise RuntimeError(f"{label} missing words with y")
    vowel_set = set(VOWEL_WORDS)
    if not any(any(word.lower() in vowel_set for word in line.split()) for line in g_lines):
        raise RuntimeError(f"{label} missing vowel-only words")

    h_blob = "\n".join(grouped["h"])
    checks = (
        (r"\d+(st|nd|rd|th)\b", "ordinal"),
        (r"\$\d", "money"),
        (r"\([A-Za-z]+\)", "parentheses"),
        (r'"[A-Za-z]+"', "straight quotes"),
        ("\u201c", "left curly quote"),
        ("\u201d", "right curly quote"),
        (r"\[[A-Za-z]+\]", "brackets"),
        (r"\.\.\.", "ellipsis"),
        ("&", "ampersand"),
        (r"#[A-Za-z]+", "hash tag"),
        (r"@[A-Za-z]+", "mention"),
    )
    for pattern, name in checks:
        if pattern.startswith("\\") or pattern.startswith("(") or pattern.startswith("["):
            found = re.search(pattern, h_blob) is not None
        elif pattern in ("&", "\u201c", "\u201d"):
            found = pattern in h_blob
        else:
            found = re.search(pattern, h_blob) is not None
        if not found:
            raise RuntimeError(f"{label} missing {name}")

    i_lines = grouped["i"]
    if sum(line == "" for line in i_lines) != 1:
        raise RuntimeError(f"{label} should contain exactly one empty line")
    if not any(line != "" and line.strip(" \t") == "" for line in i_lines):
        raise RuntimeError(f"{label} missing whitespace-only line")
    if not any(line[:1] in " \t" and line.strip(" \t") != "" for line in i_lines):
        raise RuntimeError(f"{label} missing leading whitespace")
    if not any(line[-1:] in " \t" and line.strip(" \t") != "" for line in i_lines):
        raise RuntimeError(f"{label} missing trailing whitespace")
    if not any("  " in line for line in i_lines):
        raise RuntimeError(f"{label} missing a run of spaces")
    if not any("\t" in line for line in i_lines):
        raise RuntimeError(f"{label} missing a tab")

    j_lines = grouped["j"]
    honor_hits = {name: set() for name in HONORIFICS}
    positions = {"start": 0, "middle": 0, "end": 0}
    for line in j_lines:
        parts = line.split()
        for index, word in enumerate(parts):
            key = word.lower()
            if key not in honor_hits:
                continue
            honor_hits[key].add(_honor_class(word))
            if index == 0:
                positions["start"] += 1
            elif index == len(parts) - 1:
                positions["end"] += 1
            else:
                positions["middle"] += 1
    for name, seen in honor_hits.items():
        if not {"lower", "upper", "title", "mixed"} <= seen:
            raise RuntimeError(f"{label} honorific {name} cases are {seen}")
    if min(positions.values()) < 1:
        raise RuntimeError(f"{label} honorific positions {positions}")

    k_lines = grouped["k"]
    singles = [
        line
        for line in k_lines
        if line.split() and len(line.split()) == 1 and " " not in line and "\t" not in line
    ]
    longs = [line for line in k_lines if 30 <= len(line.split()) <= 60]
    if len(singles) < 20 or len(longs) < 20:
        raise RuntimeError(
            f"{label} single-word {len(singles)} long {len(longs)} (need >= 20 each)"
        )
    return multi


def naive_baseline(line):
    return " ".join(word.capitalize() for word in line.split(" "))


def report(label, lines, expected, tags, counts, multi):
    same = sum(left == right for left, right in zip(lines, expected))
    naive = sum(right == naive_baseline(left) for left, right in zip(lines, expected))
    print(f"{label}")
    print(f"  lines: {len(lines)}")
    print(f"  multi-category: {multi}/{len(lines)} = {multi / len(lines):.4f}")
    print("  lines per category:")
    for cat in CATS:
        print(f"    {cat}: {counts[cat]}")
    empty = lines.count("")
    print(f"  empty lines: {empty}")
    print(f"  expected == input: {same / len(lines):.4f} ({same}/{len(lines)})")
    print(
        "  expected == naive baseline: "
        f"{naive / len(lines):.4f} ({naive}/{len(lines)})"
    )


def main():
    used = set()
    dev_lines, dev_tags, dev_counts, dev_multi = generate(
        random.Random(1), used, multi_target=800, emit_empty=True
    )
    hidden_lines, hidden_tags, hidden_counts, hidden_multi = generate(
        random.Random(2), used, multi_target=1200, emit_empty=True
    )

    if len(set(dev_lines)) != LINE_COUNT or len(set(hidden_lines)) != LINE_COUNT:
        raise RuntimeError("duplicate lines inside a set")
    shared = set(dev_lines) & set(hidden_lines)
    if shared != {""}:
        raise RuntimeError(f"sets share {shared!r}, expected only the empty line")

    for line in dev_lines + hidden_lines:
        if not chars_ok(line):
            raise RuntimeError(f"illegal input line: {line!r}")

    dev_expected = expected_for(dev_lines)
    hidden_expected = expected_for(hidden_lines)
    for label, inputs, outputs in (
        ("dev", dev_lines, dev_expected),
        ("hidden", hidden_lines, hidden_expected),
    ):
        if inputs.count("") != 1 or outputs[inputs.index("")] != "":
            raise RuntimeError(f"{label} empty input must appear once and expect \"\"")

    dev_multi_checked = assert_coverage("dev", dev_lines, dev_tags)
    hidden_multi_checked = assert_coverage("hidden", hidden_lines, hidden_tags)
    if dev_multi_checked != dev_multi or hidden_multi_checked != hidden_multi:
        raise RuntimeError("multi-category tally mismatch")
    if dev_multi * 3 < LINE_COUNT:
        raise RuntimeError(f"dev multi-category share too low: {dev_multi}")
    if hidden_multi * 2 < LINE_COUNT:
        raise RuntimeError(f"hidden multi-category share too low: {hidden_multi}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    outputs = {
        "inputs.txt": dev_lines,
        "expected.txt": dev_expected,
        "hidden_inputs.txt": hidden_lines,
        "hidden_expected.txt": hidden_expected,
    }
    for name, rows in outputs.items():
        if len(rows) != LINE_COUNT:
            raise RuntimeError(f"{name} has {len(rows)} lines")
        write_lines(DATA_DIR / name, rows)

    reread = {name: read_lines(DATA_DIR / name) for name in outputs}
    for name, rows in outputs.items():
        if reread[name] != rows:
            raise RuntimeError(f"{name} did not round-trip")

    print()
    report("dev", dev_lines, dev_expected, dev_tags, dev_counts, dev_multi)
    print()
    report(
        "hidden",
        hidden_lines,
        hidden_expected,
        hidden_tags,
        hidden_counts,
        hidden_multi,
    )
    print()
    print(f"input lines shared by the two sets: {len(shared)}")
    print()
    print("sha256")
    for name in outputs:
        print(f"  {name}: {sha256_file(DATA_DIR / name)}")


if __name__ == "__main__":
    main()
