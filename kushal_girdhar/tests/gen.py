import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from reference import describe, framed, load

ROOT = Path(__file__).resolve().parent

DOMAINS = {
    "release": (
        ("schema rollout", "artifact registry", "hotfix train", "release gate", "package index",
         "worker upgrade", "migration job", "feature flag", "image mirror", "dependency cache"),
        ("canary lane", "manifest signing", "installer bundle", "migration lock", "release branch",
         "rollout budget", "build stamp", "rollback marker", "package promotion", "freeze window"),
        ("compatibility", "verification", "promotion", "sign-off", "rollback", "packaging"),
    ),
    "incident": (
        ("queue backlog", "disk saturation", "payment retry", "token outage", "worker restart",
         "capacity alert", "audit delay", "dead letter queue", "pager rotation", "cache eviction"),
        ("clock drift", "quota exhaustion", "replica lag", "write stall", "batch starvation",
         "alert storm", "key rollover", "index corruption", "snapshot gap", "deadlock recovery"),
        ("triage", "follow-up", "containment", "on-call handoff", "mitigation", "root cause"),
    ),
    "network": (
        ("route leak", "packet filter", "tunnel failover", "peer session", "edge proxy",
         "service mesh", "port scan", "resolver cache", "transit link", "traffic shaping"),
        ("address lease", "fiber cut", "interconnect flap", "mesh gateway", "relay pool",
         "certificate chain", "link aggregation", "prefix filter", "split horizon", "socket drain"),
        ("packet capture", "path selection", "reconvergence", "telemetry", "probe setup", "fallback"),
    ),
    "documentation": (
        ("operator runbook", "storage guide", "deployment checklist", "query examples", "schema notes",
         "client tutorial", "cluster handbook", "support matrix", "command reference", "setup guide"),
        ("recovery manual", "configuration map", "maintainer guide", "integration notes", "admin handbook",
         "driver reference", "migration primer", "diagnostics guide", "onboarding steps", "workflow appendix"),
        ("examples", "prerequisites", "architecture", "quick start", "reference", "troubleshooting"),
    ),
}

FEATURES = {
    "small": ("and", "an", "at", "but", "by", "for", "in", "of", "on", "the", "via", "v.", "vs."),
    "edges": ("[the", "‘in", "—on", "“of", "_the", "((an", "[for", "the"),
    "endings": ("for?", "on", "of.", "via]", "and—", "v.", "vs.", "in!!", "for}", "on”"),
    "initials": ("A.B.", "Q.P", "R.S.T.U.", "W.", "É.Q", "A.BC.D.", "J.KL.MN."),
    "honorifics": ("mR", "mRS", "MS", "dR", "Dr", "ms", "mrs"),
    "apostrophe": ("o'neill", "l‘hôpital", "d'angelo", "O'BRIEN", "d'os'", "o'ßara's", "d’angelo", "o'7ops"),
    "mc": ("mcdonald", "MCBRIDE", "mccarthy", "Mcélo", "McMcGregor", "mc3lane", "mca", "mCkay", "mcthe"),
    "inline": ("api.example", "svc.a", "1.23", "K.é", "a._", "x.٢", "k.eystone", "λ.٣"),
    "mixed": ("gRPC", "GitHub", "IPv6", "_apiGW", "iSCSI", "aSync", "éXchange", "xKey"),
    "consonants": ("tcp", "bgp", "dns", "rt", "sctp", "ſsh", "Kvm", "nginx", "vrrp"),
    "slash": ("read/in/write", "in/out", "drop/and/forward", "cache//origin", "https://edge/path", "on//off-link"),
    "hyphen": ("end-to-end", "two--phase", "store-and-forward", "-to-standby", "preflight-", "fleet–wide"),
    "expansion": ("ßtunnel", "ﬃle", "ǰob", "ևroute", "ŉode", "ΐris", "İn", "ıf", "ſync"),
    "sigma": ("ΟΣ", "ΑΣ’", "Σ", "ΟΣ᾽Α", "ΟΣ́", "ΟΣʰ!", "ΟΣʰΑ", "Α-Σ"),
    "boundary": ("[ſo", "_edge", "²probe", "\u0301alpha", "👩‍💻logs", "a\u0301.the", "K.node", "𐐷ops"),
    "separators": ("\t", "\u00a0", "\u2007", "\u202f", "\u3000", "\x1c", "  ", "\v", "\u2028"),
    "subphrase": (":", ".", "!", "?", "-", "–", "‒", "—", "―", ";", "…"),
    "nested": ("read-only/in-band", "rollback-and/retry", "a//b-on-c/d", "and/or-not", "McIn/Out-of-band",
               "d'ops/read-and-write", "a--b/c-d", "/by/route-of/"),
}

CELLS = (
    "small", "edges", "initials", "honorifics", "apostrophe", "mc", "inline", "mixed",
    "consonants", "compounds", "expansion", "sigma", "boundary", "separators", "subphrase", "nested",
)


def feature(name):
    return random.choice(FEATURES[name])


def make_record(cell, domain, split):
    visible, hidden, actions = DOMAINS[domain]
    subject = random.choice((visible, hidden)[split])
    action = random.choice(actions)
    small = feature("small")
    if cell == "small":
        return f"{action} {small} {subject}" if random.randrange(2) else f"{subject} {small} {action}"
    if cell == "edges":
        return f"{feature('edges')} {subject} {action} {feature('endings')}"
    if cell == "initials":
        return f"{subject} {action} by {feature('initials')}".upper()
    if cell in ("honorifics", "apostrophe", "mc"):
        record = f"{action} by {feature(cell)} on {subject}"
        return record.upper() if random.randrange(4) == 0 else record
    if cell in ("inline", "mixed", "consonants", "expansion", "boundary"):
        return f"{subject} {action} via {feature(cell)}"
    if cell == "compounds":
        return f"{action} for {feature(random.choice(('slash', 'hyphen')))} {subject}"
    if cell == "sigma":
        return f"{subject} {action} via {feature('sigma')}".upper()
    if cell == "separators":
        gap = feature("separators")
        return random.choice(("", gap)) + gap.join((subject, small, action)) + random.choice(("", gap))
    if cell == "subphrase":
        return f"{subject}{feature('subphrase')}{random.choice((' ', '  ', chr(9)))}{small} {action}"
    if cell == "nested":
        return f"{subject} {action} {feature('subphrase')}{random.choice((' ', '  '))}{feature('nested')}"
    raise ValueError(cell)


def generate(reference):
    random.seed(1)
    seen_inputs, seen_outputs = set(), set()
    for split in range(2):
        pairs, counts = [], Counter()
        for index, cell in enumerate(CELLS):
            for row in range(125):
                domain = tuple(DOMAINS)[(row + index) % len(DOMAINS)]
                for _ in range(10_000):
                    record = make_record(cell, domain, split)
                    expected = reference(record)
                    if record not in seen_inputs and expected not in seen_outputs:
                        break
                else:
                    raise RuntimeError(f"coverage cell exhausted: {cell}/{domain}")
                seen_inputs.add(record)
                seen_outputs.add(expected)
                counts[cell, domain] += 1
                pairs.append((record, expected))
        random.shuffle(pairs)
        yield pairs, counts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    report = {"reference": describe(), "seed": 1, "splits": {}}
    for split, (pairs, counts) in zip(("visible", "hidden"), generate(load()), strict=True):
        rows, answers = zip(*pairs, strict=True)
        prefix = "hidden_" if split == "hidden" else ""
        files = {}
        for label, records in (("inputs", rows), ("expected", answers)):
            payload = framed(records)
            assert b"\r" not in payload and payload.count(b"\n") == len(pairs) == 2000
            name = prefix + label + ".txt"
            (args.output / name).write_bytes(payload)
            files[name] = hashlib.sha256(payload).hexdigest()
        report["splits"][split] = {
            "files": files,
            "coverage": {cell: {domain: counts[cell, domain] for domain in DOMAINS} for cell in CELLS},
        }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
