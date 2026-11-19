"""Generate 1200x630 social preview images into public/og/.

Run when an article title or the brand changes:
    cd website && python scripts/og_images.py
Needs: pip install playwright && playwright install chromium (or set CHROME_PATH).
Images contain only text and livery motifs (chequer, kerb): no photographs, logos or third-party marks.
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
               face("Sans", "barlow", 400), face("Sans", "barlow", 600)]) + """
body{margin:0;width:1200px;height:630px;background:#14191C;color:#E8E5DF;font-family:Sans;box-sizing:border-box;display:flex;flex-direction:column}
.chq{height:18px;background-color:#E8E5DF;background-image:linear-gradient(45deg,#14191C 25%,transparent 25%,transparent 75%,#14191C 75%),linear-gradient(45deg,#14191C 25%,transparent 25%,transparent 75%,#14191C 75%);background-size:18px 18px;background-position:0 0,9px 9px}
.kerb{height:10px;background:repeating-linear-gradient(90deg,#B58A52 0 34px,#E8E5DF 34px 68px)}
.top{background:#18252C;padding:22px 72px;display:flex;align-items:center;gap:16px}
.plate{font-family:Display;font-weight:700;font-style:italic;font-size:34px;background:#B58A52;color:#14191C;padding:2px 12px;transform:skewX(-12deg)}
.mast{font-family:Display;font-weight:700;font-style:italic;font-size:40px;color:#F6F5F1;text-transform:uppercase;letter-spacing:1px}
.tag{font-size:20px;color:#D4AA6E}
.main{padding:40px 72px 0;flex:1;display:flex;flex-direction:column}
.kicker{font-family:Display;font-weight:700;font-size:26px;color:#D4AA6E;text-transform:uppercase;letter-spacing:2px}
h1{font-family:Display;font-weight:700;font-style:italic;font-size:92px;line-height:0.95;margin:10px 0 0;color:#F6F5F1;text-transform:uppercase}
.dek{font-size:30px;line-height:1.3;color:#E8E5DF;margin-top:18px;max-width:1000px}
.foot{margin-top:auto;padding:16px 0 22px;display:flex;justify-content:space-between;font-size:20px;color:#9CA5A2}
"""

def page(kicker, title, dek):
    return f"""<html><head><style>{CSS}</style></head><body>
<div class="chq"></div><div class="top"><span class="plate">F1</span><div><div class="mast">Moneyball</div><div class="tag">{B['tagline']}</div></div></div><div class="kerb"></div>
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
