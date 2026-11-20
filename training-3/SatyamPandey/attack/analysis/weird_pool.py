"""usage: weird_pool.py <count> <seed> <out>  -- unique random titles with weird word families"""
import random, sys
n, seed, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
rnd = random.Random(seed)
plain = "river garden quiet bright silver morning window journey story paper blue mountain clock summer dream small city music shadow open world light history time".split()
small = "a an and as at but by en for if in of on or the to v v. via vs vs.".split()
weird = [
    "v1.2", "v2.0.1", "_dream", "__init__", "dream_", "Mcx-", "mcdonald", "McDONALD", "MCKAY", "macintosh",
    "ıstanbul", "İstanbul", "éclair", "ÉCOLE", "naïve", "straße", "ǅungla", "ﬁne", "Ωmega", "über",
    "d'arcy", "D'ARCY", "o'neill", "l’amour", "rock'n'roll", "'tis", "it's", "don't",
    "X-RAY", "x-ray", "TCP/IP", "and/or", "a/b", "w/o", "e-mail", "E-MAIL", "co-op", "self-made",
    "BBC", "NASA", "UK", "U.S.", "u.s.a.", "A.B.", "e.g.", "i.e.", "etc.", "Ph.D.", "J.R.R.",
    "iPhone", "eBay", "macOS", "YouTube", "jQuery", "mRNA",
    "mr", "Mr.", "MRS", "ms.", "dr", "DR.", "st.", "jr.",
    "3rd", "21st", "1990s", "100%", "$5", "#1", "@home", "c++", "c#", ".net", "node.js",
    "http://ex.com/a", "www.site.org", "a@b.com", "file.txt",
    "(hello)", "[the", "end]", '"quoted"', "“curly”", "‘single’", "«guillemet»", "¿qué?", "¡hola!",
    "—", "–", "-", "...", "…", ":", ";", "!", "?", "&", "+", "*", "/", "\\", "|", "~", "^",
    "summer!", "time:", "world;", "as!", "by.", "of?", "the:", "a-", "-the",
    "OF", "AT", "IF", "BY", "THE", "AND", "VIA", "VS",
    "😀", "★", "日本", "ü", "x", "y", "ab", "AB", "aB", "Ab",
]
seps = [" "] * 30 + ["  ", "\t", "\u00a0", " - ", " — ", ": ", "/", "-", " . ", "\u2009", "\u3000"]
def word():
    r = rnd.random()
    w = rnd.choice(plain) if r < .35 else rnd.choice(small) if r < .6 else rnd.choice(weird)
    c = rnd.random()
    return w.upper() if c < .12 else w.title() if c < .22 else w.capitalize() if c < .27 else w
seen = set()
with open(out, "w", encoding="utf-8", newline="\n") as f:
    while len(seen) < n:
        k = rnd.randint(1, 9)
        t = word()
        for _ in range(k - 1):
            t += rnd.choice(seps) + word()
        if rnd.random() < .05: t = " " + t
        if rnd.random() < .05: t = t + rnd.choice([" ", "  ", "\t", "."])
        if "\n" in t or "\r" in t or t in seen: continue
        seen.add(t); f.write(t + "\n")
