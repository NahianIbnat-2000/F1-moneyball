# Working paper: Does Money Buy Speed?

LaTeX source for the F1 Moneyball working paper by Nahian Ibnat.
Website version: https://nahianibnat-2000.github.io/F1-moneyball/research/does-money-buy-speed

Every number, table and figure is generated from the datasets the website publishes
(`website/public/data`). Nothing is typed by hand.

## Build

From the repository root:

```bash
pip install -e .
python paper/make_assets.py        # writes paper/generated/ (numbers.tex, tables, figures)
cd paper && latexmk -pdf main.tex  # writes paper/main.pdf
```

To rebuild from fresh data first, run `python -m f1moneyball.pipeline all`.

## Files

| File | What it is |
|---|---|
| `main.tex` | The paper |
| `references.bib` | References |
| `make_assets.py` | Reads the published data and writes everything in `generated/` |
| `generated/numbers.tex` | Every number in the text, as LaTeX commands (e.g. `\CoefTurnFe`) |
| `generated/table*.tex` | Table rows |
| `generated/fig*.pdf` | Figures |

References use APA 7th edition through `biblatex-apa` and `biber` (`latexmk` runs biber for you;
on Ubuntu: `sudo apt install texlive-bibtex-extra biber`). Overleaf supports this out of the box.

If the data change, rerun both steps. The dataset versions printed in the paper's
"Data and code availability" section show which data the PDF was built from.

You can also open `main.tex` in Overleaf: upload the whole `paper` folder, including `generated/`.
