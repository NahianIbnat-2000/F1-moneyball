"""Generate 1200x630 social preview images into public/og/.

Run when an article title or the brand changes:
    cd website && python scripts/og_images.py
Needs: pip install playwright && playwright install chromium (or set CHROME_PATH).
Images contain only text and livery motifs (kerb): no photographs, logos or third-party marks.
"""
import json, os, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
fonts = ROOT / "node_modules" / "@fontsource"
data = json.loads(subprocess.check_output(["npx", "tsx", "scripts/pages-json.ts"], cwd=ROOT, text=True))
B = data["brand"]

def face(fam, pkg, w, style="normal"):
    f = fonts / pkg / "files" / f"{pkg}-latin-{w}-{style}.woff2"
    return f"@font-face{{font-family:'{fam}';src:url('file://{f}') format('woff2');font-weight:{w};font-style:{style}}}"

CSS = "".join([face("Display", "barlow-condensed", 700), face("Display", "barlow-condensed", 700, "italic"),
               face("Sans", "barlow", 400), face("Sans", "barlow", 600),
               face("SrcSerif", "source-serif-4", 600), face("SrcSerif", "source-serif-4", 400, "italic"),
               face("Mono", "jetbrains-mono", 400)]) + """
body{margin:0;width:1200px;height:630px;background:#0A0D10;color:#E4E1D8;font-family:Sans;box-sizing:border-box;display:flex;flex-direction:column}
.status{background:#0A0D10;border-bottom:1px solid #252E36;padding:10px 72px;font-family:Mono;font-size:16px;letter-spacing:2px;text-transform:uppercase;color:#98A2A8}
.status b{display:inline-block;width:10px;height:10px;border-radius:50%;background:#E5372A;margin-right:10px}
.kerb{height:8px;background:repeating-linear-gradient(90deg,#E5372A 0 30px,#F6F4EE 30px 60px)}
.top{background:#0E1317;padding:20px 72px;display:flex;align-items:center;gap:16px}
.plate{font-family:Display;font-weight:700;font-style:italic;font-size:34px;background:#E5372A;color:#fff;padding:2px 12px;transform:skewX(-12deg)}
.mast{font-family:Display;font-weight:700;font-style:italic;font-size:40px;color:#F6F4EE;text-transform:uppercase;letter-spacing:1px;line-height:1}
.tag{font-family:SrcSerif;font-style:italic;font-size:21px;color:#98A2A8;margin-top:4px}
.main{padding:42px 72px 0;flex:1;display:flex;flex-direction:column}
.kicker{font-family:Mono;font-size:20px;color:#F7B54A;text-transform:uppercase;letter-spacing:3px}
h1{font-family:SrcSerif;font-weight:600;font-size:76px;line-height:1.02;margin:14px 0 0;color:#F6F4EE;letter-spacing:-1px}
.dek{font-family:SrcSerif;font-style:italic;font-size:29px;line-height:1.3;color:#E4E1D8;margin-top:18px;max-width:1000px}
.foot{margin-top:auto;padding:16px 0 22px;border-top:1px solid #252E36;display:flex;justify-content:space-between;font-family:Mono;font-size:16px;letter-spacing:1px;text-transform:uppercase;color:#98A2A8}
"""

def page(kicker, title, dek):
    return f"""<html><head><style>{CSS}</style></head><body>
<div class="status"><b></b>Research terminal</div><div class="top"><span class="plate">F1</span><div><div class="mast">Moneyball</div><div class="tag">{B['tagline']}</div></div></div><div class="kerb"></div>
<div class="main"><div class="kicker">{kicker}</div><h1>{title}</h1><div class="dek">{dek}</div>
<div class="foot"><span>{B['positioning']}</span><span>{B['series']}</span></div></div></body></html>"""

out = ROOT / "public" / "og"; out.mkdir(parents=True, exist_ok=True)
jobs = [("default", B["series"], B["headline"], "Formula 1 is a competition for milliseconds, but behind every performance is an economic decision.")]
jobs += [(a["slug"], a["module"], a["title"], a["dek"]) for a in data["articles"]]
with sync_playwright() as p:
    kw = {"executable_path": os.environ["CHROME_PATH"]} if os.environ.get("CHROME_PATH") else {}
    b = p.chromium.launch(args=["--no-sandbox", "--allow-file-access-from-files"], **kw)
    pg = b.new_page(viewport={"width": 1200, "height": 630})
    for name, k, t, d in jobs:
        html = ROOT / "scripts" / "_og.html"; html.write_text(page(k, t, d))
        pg.goto(f"file://{html}"); pg.wait_for_timeout(300)
        pg.screenshot(path=str(out / f"{name}.png")); print("wrote", name)
    html.unlink(); b.close()
