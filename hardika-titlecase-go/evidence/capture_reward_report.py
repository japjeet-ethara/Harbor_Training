import argparse
import html
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("jobs", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--job", choices=("oracle", "nop", "replay"))
parser.add_argument("--host", default="Docker backend")
args = parser.parse_args()
cards = []
for job in (args.job,) if args.job else ("oracle", "nop", "replay"):
    path, = sorted((args.jobs / job).glob("*/verifier/reward.json"))
    data = json.loads(path.read_text(encoding="utf-8"))
    trial_path = html.escape(path.relative_to(args.jobs).as_posix())
    raw = html.escape(json.dumps(data, indent=2))
    cards.append(f"<section><h2>{job}</h2><p>{trial_path}</p><pre>{raw}</pre></section>")

page = """<!doctype html>
<meta charset="utf-8">
<title>Harbor titlecase-go reward records</title>
<style>
*{box-sizing:border-box}
body{font:16px Segoe UI,sans-serif;color:#182635;background:#f2f5f8;margin:0;padding:48px 54px}
h1{font-size:36px;letter-spacing:-.03em;margin:0 0 9px}
h2{font-size:23px;margin:0 0 10px}
header p{margin:0;color:#4d5c6d}
main{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:28px}
section{background:white;border:1px solid #c7d1dc;border-radius:12px;padding:21px 18px}
section p{font:13px Consolas,monospace;margin:0 0 13px;overflow-wrap:anywhere;color:#3e5268}
pre{font:15px/1.55 Consolas,monospace;padding:14px;background:#eaf1f7;border-radius:8px;overflow-wrap:anywhere;white-space:pre-wrap}
</style>
<header><h1>Harbor titlecase-go reward records</h1>
<p>Harbor 0.26.0 · HOST_PLATFORM · Separate offline verifier</p></header>
<main>""" + "".join(cards) + "</main>\n"
page = page.replace("HOST_PLATFORM", html.escape(args.host))
if args.job:
    page = page.replace("repeat(3,minmax(0,1fr))", "minmax(0,540px)")
args.output.write_text(page, encoding="utf-8")
