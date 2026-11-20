#!/usr/bin/env python3
"""Generate a pool of N unique random titles with tricky edge cases."""

import random
import sys


def build_word_pool():
    small_words = [
        "a", "an", "and", "as", "at", "but", "by", "en", "for", "if",
        "in", "of", "on", "or", "the", "to", "v", "v.", "via", "vs", "vs."
    ]
    mc_words = [
        "mcdonald", "McDonald", "MCQUEEN", "Mcx-", "mcclure", "McX-",
        "mc", "Mc", "MC", "mcmillan", "Macintosh", "MacDonald"
    ]
    apos_words = [
        "d'arcy", "d'angelo", "l'oreal", "l'amour", "o'neil", "o'clock",
        "o'connor", "d'Artagnan", "O'Reilly", "L'Amour", "don't", "won't"
    ]
    honorifics = ["mr", "mrs", "ms", "dr", "Mr", "Mrs", "Ms", "Dr"]
    acronyms = [
        "HTML", "XML", "TCP/IP", "LaTeX", "LaTeX;", "BBC", "BBC:", "SQL",
        "BRR", "PhD", "USA", "IBM", "NATO", "OS", "IP", "X-RAY", "R2-D2", "24/7"
    ]
    uc_elsewhere = [
        "macOS", "iPhone", "iPad", "eBay", "YouTube", "MySQL", "JavaScript",
        "TypeScript", "DevOps", "OpenAI", "Node.js"
    ]
    dotted_initials = [
        "A.", "B.", "C.", "U.S.A.", "e.g.", "i.e.", "v._", "X.", "J.K.",
        "Ph.D.", "a.b.c", "v1.2", "v2.0.1"
    ]
    unicode_words = [
        "ıstanbul", "café", "naïve", "Ångström", "über", "résumé", "smörgåsbord",
        "coöperate", "señor", "façade", "piñata", "fiancée", "château"
    ]
    hyphen_slash = [
        "state-of-the-art", "built-in", "twenty-one", "user-friendly", "up-to-date",
        "and/or", "input/output", "client/server", "win/win", "c/o"
    ]
    punct_wrapped = [
        "_dream", "dream_", "*love*", "[in]", "(the)", "{art}", "\"quote\"",
        "'single'", "“smart”", "‘curly’", "!loud!", "?query?", "end/"
    ]
    subphrase_punct = [":", ";", ".", "!", "?", " -", " --", " –", " —"]
    whitespace_variants = [" ", "  ", "\t", "\u00a0"]

    general_words = [
        "world", "history", "summer", "time", "science", "garden", "fire",
        "peace", "letter", "river", "father", "machine", "home", "leading",
        "journey", "art", "music", "mountain", "ring", "rings", "secret",
        "tale", "house", "return", "north", "deep", "space", "future",
        "code", "learning", "model", "agent", "system", "network"
    ]

    all_categories = [
        small_words, mc_words, apos_words, honorifics, acronyms,
        uc_elsewhere, dotted_initials, unicode_words, hyphen_slash,
        punct_wrapped, general_words
    ]
    return all_categories, subphrase_punct, whitespace_variants


def generate_title(rng, categories, subphrase_punct, whitespace_variants):
    num_words = rng.randint(1, 8)
    chosen = []
    for _ in range(num_words):
        cat = rng.choice(categories)
        w = rng.choice(cat)
        # Random case variation occasionally
        r = rng.random()
        if r < 0.08:
            w = w.upper()
        elif r < 0.16:
            w = w.lower()
        chosen.append(w)

    # Insert subphrase punctuation between some words
    out_parts = []
    for i, w in enumerate(chosen):
        out_parts.append(w)
        if i < len(chosen) - 1:
            if rng.random() < 0.15:
                p = rng.choice(subphrase_punct)
                out_parts.append(p)
            # Pick separator
            sep = rng.choice(whitespace_variants) if rng.random() < 0.1 else " "
            out_parts.append(sep)

    return "".join(out_parts)


def main():
    if len(sys.argv) != 4:
        print("Usage: make_pool.py <count> <seed> <out.txt>", file=sys.stderr)
        sys.exit(1)

    count = int(sys.argv[1])
    seed = int(sys.argv[2])
    out_file = sys.argv[3]

    rng = random.Random(seed)
    categories, subphrase_punct, whitespace_variants = build_word_pool()

    seen = set()
    lines = []

    # Include mandatory canonical cases from instructions
    seed_cases = [
        "BBC: OF at Mcx- if summer time by",
        "v._ music! world - d'arcy",
        "X. TCP/IP history as! X-RAY",
        "the lord of the rings",
        "d'artagnan and o'malley",
        "l'oreal end/  \"by\"",
        "101st machine PhD SCIENCE Home. -leading *love* art OF",
        "MOUNTAIN ― BRR BY V. DAY NODE.JS\tLOVE THE-END",
        "rings mcdonald",
        "RETURN. R2-D2 HOUSE",
        "ıstanbul cafe",
        "_dream world",
        "v1.2 release notes"
    ]
    for sc in seed_cases:
        if sc not in seen:
            seen.add(sc)
            lines.append(sc)

    while len(lines) < count:
        t = generate_title(rng, categories, subphrase_punct, whitespace_variants)
        if t not in seen:
            seen.add(t)
            lines.append(t)

    with open(out_file, "w", encoding="utf-8", newline="\n") as f:
        for line in lines:
            f.write(line + "\n")

    print(f"Generated {len(lines)} unique titles to {out_file} (seed={seed})")


if __name__ == "__main__":
    main()
