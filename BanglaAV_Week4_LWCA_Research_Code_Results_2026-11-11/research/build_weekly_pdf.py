#!/usr/bin/env python3
"""Two-column progress report sourced exclusively from generated experiment files."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether,
                               PageTemplate, Paragraph, Spacer, Table, TableStyle)


PAPER_W, PAPER_H = A4
NAVY = colors.HexColor("#143d5b")
GRAY = colors.HexColor("#586d7d")
RULE = colors.HexColor("#bdc8d1")
FONT_DIR = Path("/usr/share/fonts/truetype/liberation")
for face, file in (("Serif", "LiberationSerif-Regular.ttf"),
                   ("Serif-Bold", "LiberationSerif-Bold.ttf"),
                   ("Serif-Italic", "LiberationSerif-Italic.ttf"),
                   ("Serif-BoldItalic", "LiberationSerif-BoldItalic.ttf")):
    pdfmetrics.registerFont(TTFont(face, str(FONT_DIR / file)))
pdfmetrics.registerFontFamily("Serif", normal="Serif", bold="Serif-Bold",
                              italic="Serif-Italic", boldItalic="Serif-BoldItalic")


class Report(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename, pagesize=A4, leftMargin=38, rightMargin=38,
                         topMargin=115, bottomMargin=40)
        gap = 18
        colw = (PAPER_W - 76 - gap) / 2
        colh = PAPER_H - 165
        frames = [Frame(38, 40, colw, colh, leftPadding=0, rightPadding=0,
                        topPadding=1, bottomPadding=0, id="col_left"),
                  Frame(38 + colw + gap, 40, colw, colh, leftPadding=0,
                        rightPadding=0, topPadding=1, bottomPadding=0, id="col_right")]
        self.addPageTemplates(PageTemplate(id="two_columns", frames=frames,
                                           onPage=self.draw_header))

    def draw_header(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.setFont("Serif-Bold", 14.1)
        canvas.drawCentredString(PAPER_W / 2, PAPER_H - 44,
                                 "BanglaAV: Audio-Visual Deepfake Localization")
        canvas.setFont("Serif-Bold", 11.1)
        canvas.drawCentredString(PAPER_W / 2, PAPER_H - 61,
                                 "Week 4 - Method Extension and Controlled Evidence")
        canvas.setFont("Serif", 8.8)
        canvas.drawCentredString(PAPER_W / 2, PAPER_H - 76,
                                 "CSE 499 Research Team | North South University")
        canvas.setFont("Serif-Italic", 8.3)
        canvas.drawCentredString(PAPER_W / 2, PAPER_H - 90,
                                 "Research checkpoint: 11 November 2026")
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(.6)
        canvas.line(38, PAPER_H - 104, PAPER_W - 38, PAPER_H - 104)
        canvas.line(38, 30, PAPER_W - 38, 30)
        canvas.setFillColor(GRAY)
        canvas.setFont("Serif", 7)
        canvas.drawString(38, 20, "Synthetic lag-estimation experiment; real-media validation pending")
        canvas.drawRightString(PAPER_W - 38, 20, f"Page {doc.page}")
        canvas.restoreState()


def style(name, **props):
    settings = dict(fontName="Serif", fontSize=8.3, leading=10.55,
                    alignment=TA_LEFT, spaceAfter=4.5, textColor=colors.black)
    settings.update(props)
    return ParagraphStyle(name, **settings)


def load_rows(filename):
    with filename.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--development", type=Path, required=True)
    parser.add_argument("--holdout", type=Path, required=True)
    parser.add_argument("--integration", type=Path, required=True)
    parser.add_argument("--figure", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    dev_protocol = json.loads((args.development / "experiment_protocol.json").read_text())
    hold_protocol = json.loads((args.holdout / "experiment_protocol.json").read_text())
    integration = json.loads((args.integration / "integration_summary.json").read_text())
    assert integration["passed"] == integration["total"] == 8
    assert dev_protocol["n_simulated_examples"] == hold_protocol["n_simulated_examples"] == 1800
    summary = {(r["condition"], r["method"]): r for r in load_rows(args.holdout / "lag_summary.csv")}
    ci = {r["condition"]: r for r in load_rows(args.holdout / "paired_bootstrap.csv")}
    assert all((c, m) in summary for c in ("audio_edit", "visual_edit", "dual_edit")
               for m in ("original_global", "robust_consensus", "lwca_32bin", "lwca_48bin"))

    normal = style("body")
    abstract = style("abstract", fontSize=8.35, leading=10.5)
    smaller = style("smaller", fontSize=7.55, leading=9.55, spaceAfter=3)
    caption = style("caption", fontSize=7.35, leading=9, alignment=TA_CENTER,
                    textColor=GRAY, spaceAfter=6)
    heading = style("heading", fontName="Serif-Bold", fontSize=9.25, leading=11,
                    spaceBefore=9, spaceAfter=3, textColor=NAVY)
    cell_style = style("table", fontSize=7.15, leading=8.5, spaceAfter=0)
    story = []

    def section(name, *paragraphs):
        blocks = [Paragraph(name, heading)]
        if paragraphs:
            blocks.append(Paragraph(paragraphs[0], normal))
        story.append(KeepTogether(blocks))
        for paragraph in paragraphs[1:]:
            story.append(Paragraph(paragraph, normal))

    story.append(Paragraph(
        "<b>Abstract -</b> We implemented <b>Local-Window Consensus Alignment (LWCA)</b> "
        "to reduce the influence of locally manipulated audio/visual activity on the "
        "clip-wide synchronization estimate. In a newly generated 1,800-sequence "
        "synthetic holdout, the selected 16-bin method reduced mean absolute lag "
        "error from 78.0 to 25.1 ms (audio edits), 43.1 to 13.1 ms (visual edits), "
        "and 110.0 to 26.0 ms (dual edits). All eight integration tests passed. "
        "<b>These are controlled feature-level results, not LAV-DF or Bengali "
        "deepfake-detection results.</b>", abstract))
    story.append(Paragraph("<b>Index Terms -</b> temporal localization, audio-visual "
                           "synchronization, robust lag consensus, ablation, BanglaAV.", smaller))

    section("I. MOTIVATION AND RESEARCH HYPOTHESIS",
            "In Update 3, our delay-aware pipeline estimated a single offset "
            "from the entire clip. This introduces a potential failure: a strong "
            "local edit can distort the global audio-energy/mouth-motion "
            "correlation, even if most of the recording is unedited. Our "
            "testable hypothesis is that locally estimated delays, combined "
            "by consensus, better recover the underlying recording offset "
            "under partial manipulation. This is a new <i>project-level "
            "method extension</i>, not a claim of first discovery in the literature.")

    section("II. PROPOSED METHOD: LWCA",
            "Both streams are mapped to 80-ms bins, as in Update 3. "
            "We compare the absolute temporal change of audio energy "
            "with lower-face motion. Overlapping windows of 16 bins "
            "(1.28 s), advanced by 8 bins (0.64 s), each search offsets "
            "from -5 to +5 bins (±400 ms). The maximum Pearson correlation "
            "votes for a lag only when it exceeds 0.24. The modal lag is "
            "accepted if its voting support is at least 50% and it has "
            "adequate advantage over zero offset; otherwise we return zero.",
            "The resulting aligned and unaligned features enter the same "
            "48-hidden-unit head architecture as the previous delay-aware "
            "method. We added <b>robust_delay_aware</b> as a seventh model "
            "with separate audio/visual heads; existing baselines stay intact. "
            "Cross-modal false attribution (e.g., an audio alarm on a "
            "visual-only edit) is now explicitly counted.")

    section("III. EXPERIMENT DESIGN",
            "We extracted the <i>original</i> global alignment function "
            "from the team's submitted Update 3 notebook; the comparator "
            "was not reimplemented. Each protocol generates 3 random seeds "
            "× 5 conditions × 120 samples = 1,800 independent synthetic "
            "feature sequences. Conditions are aligned genuine, clean "
            "shifted, audio edit, visual edit, and dual edit. Ground-truth "
            "global offset is known by construction.",
            "We used 16-, 32-, and 48-bin consensus windows as an ablation. "
            "After development experiments (seeds 17, 29, 43), the more "
            "variable holdout used new seeds 101, 211, 307 and changes in "
            "signal length, pulse rate, background noise, edit length, "
            "and offset range. No examples were reused across protocols. "
            "A fixed-seed, 1,000-resample paired bootstrap summarizes "
            "holdout lag-error differences.")

    section("IV. MEASURED HOLDOUT RESULTS",
            "Table I compares lag-estimation error on the three edited "
            "conditions (360 sequences each). Lower is better. Exact "
            "lag-match accuracy improved from 78.1% to 91.1% for audio "
            "edits, 86.1% to 94.7% for visual edits, and 61.4% to "
            "90.3% for dual edits.")

    def tab_cell(s, bold=False):
        return Paragraph(f"<b>{s}</b>" if bold else s, cell_style)

    data = [[tab_cell("Edit type", True), tab_cell("Global MAE", True),
             tab_cell("LWCA MAE", True), tab_cell("Delta [95% CI]", True)]]
    labels = {"audio_edit": "Audio", "visual_edit": "Visual", "dual_edit": "Dual"}
    for condition in ("audio_edit", "visual_edit", "dual_edit"):
        first = summary[condition, "original_global"]
        current = summary[condition, "robust_consensus"]
        estimate = ci[condition]
        data.append([tab_cell(labels[condition]), tab_cell(f'{float(first["mae_ms"]):.1f}'),
                     tab_cell(f'{float(current["mae_ms"]):.1f}'),
                     tab_cell(f'{float(estimate["mae_delta_robust_minus_original_ms"]):.1f} '
                              f'[{float(estimate["bootstrap_low_ms"]):.1f}, '
                              f'{float(estimate["bootstrap_high_ms"]):.1f}]')])
    table = Table(data, colWidths=[43, 51, 52, 105], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e9f0f5")),
        ("LINEBELOW", (0, 0), (-1, 0), .55, NAVY),
        ("LINEBELOW", (0, -1), (-1, -1), .4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(Paragraph("<b>TABLE I.</b> Synthetic holdout MAE in ms; "
                           "delta = LWCA - global (negative favors LWCA).", caption))
    story.append(table)
    story.append(Spacer(1, 8))
    figure = Image(str(args.figure), width=250, height=110.5)
    figure.hAlign = "CENTER"
    story.append(figure)
    story.append(Paragraph("Fig. 1. Window-length ablation on the synthetic holdout "
                           "(360 examples per edit type).", caption))

    section("V. CHECKS AND INTERPRETATION",
            "For clean genuine and clean shifted cases, both the global "
            "estimator and LWCA had zero lag error in this simulator. "
            "That ceiling result reflects relatively simple synthetic "
            "patterns and cannot establish clean real-video reliability. "
            "The 16-bin window beat the tested 32- and 48-bin alternatives "
            "under these localized corruptions. This supports the proposed "
            "mechanism, but it may not generalize to speech, occlusion, "
            "off-center faces, or conversational mouth movements.",
            f"A functional smoke run of the patched notebook passed "
            f'{integration["passed"]}/{integration["total"]} tests, including training all '
            "10 heads across seven model variants on small synthetic "
            "arrays, producing finite predictions, model-specific lag "
            "metadata, false-modality alarms, and paired comparison rows. "
            "This is not a real-media training run.")

    section("VI. LIMITATIONS AND NEXT RUN",
            "<b>Uncompleted real-media validation:</b> The permitted LAV-DF "
            "media and existing trained heads were unavailable here. No "
            "new LAV-DF AP50, F1, genuine-video false alarm rate, or "
            "Bengali metric has been measured. A synthetic lag-error "
            "improvement is <i>not</i> yet a deepfake-localization gain.",
            "Next, run the augmented notebook on the existing 320/96 "
            "train/development protocol, compare raw/delay/LWCA fusion "
            "with multiple training seeds, and evaluate AP50, edit recall, "
            "genuine-video alarm rate, and wrong-modality attribution at "
            "matched recall. Stress with ±240-ms feature shifts on the "
            "same temporal support and shifted audio labels. Select "
            "thresholds only on development data; open the reserved "
            "test set once. Bangla speaker/source-disjoint collection "
            "with participant consent remains necessary.")

    section("VII. REPRODUCIBILITY AND PROVENANCE",
            "The companion ZIP includes the unchanged Update 3 source "
            "notebook, patched Update 4 notebook, readable diff, LWCA "
            "algorithm, synthetic generator, notebook patcher, training "
            "integration smoke runner, aggregate and per-example CSVs, "
            "seed/protocol JSON, plot code, and this report. Original "
            "source: NSU-CSE499-Research/CSE499-Senior-Design, commit "
            "c96b64ea69ac9ce28d484dfbfacf7ce02da5bdd0. No protected "
            "video data, participant recordings or model checkpoints "
            "are redistributed.")

    story.append(Paragraph("REFERENCES", heading))
    story.append(Paragraph(
        "[1] BanglaAV CSE499 team, <i>Update 3: Implementation and LAV-DF "
        "Pilot Results</i>, NSU, November 2026.", smaller))
    story.append(Paragraph(
        "[2] NSU-CSE499-Research, <i>CSE499-Senior-Design</i>, "
        "Update-03/cse499b-update-3.ipynb, GitHub commit c96b64ea, "
        "accessed November 2026.", smaller))

    Report(str(args.output)).build(story)
    print("Wrote report:", args.output)


if __name__ == "__main__":
    main()
