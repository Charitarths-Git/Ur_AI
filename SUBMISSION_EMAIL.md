# Submission email draft

Draft only; no email sent. Send after the final remote-HEAD verification succeeds.
No attachment package has been prepared, so the email links to conversation records.

## A. Verified facts for the email

- Start at [REPORT.md](REPORT.md), [README.md](README.md),
  [examples](examples/) and [evaluation results](eval/results/).
- Structural period-heading detection prevents dated footers/body labels from
  erasing the table; standalone JSON evaluation checks actual nesting, schema,
  values and separate CSV consistency. Focused regressions are in tests/test_p14.py.
- Supplied human-verified development page:86/86 cells,43/43 fully correct rows
  in CSV and JSON,20/20 evaluable accounting checks; sources: page4_report.json
  and notes/p14_verification.json. This is not held-out accuracy.
- Five new official pages: two development issuers, three held out before
  predictions. Frozen original/candidate both262/262 held-out cells and129/131
  fully correct rows. GT is AI_DRAFT, not human-verified or independently checked.
  Four initial transcription errors were corrected after enlarged-image review;
  initial artifacts are retained. Sources: benchmarks/manifest.json,
  benchmarks/README.md, eval/results/benchmark/report.json.
- Pdfplumber held-out cells250/262; hierarchy/types unsupported. Median candidate
  times on the three held-out pages13.70–41.78ms versus101.46–424.13ms for this
  fixed baseline, with per-page IQRs and actual samples in benchmark/report.json.
  Same machine, five repetitions after one warmup, PDF I/O included; evaluation
  excluded. Candidate is not uniformly faster than the original parser.
- x=.3H supplied-page mean cell accuracy .9360→1.0000, but y=.5H parents
  .8581→.7535. Seed-11 split, weak-indentation hierarchy and ontology disagreements
  remain. Source: eval/results/p14/comparison.md. Accounting tolerance unchanged.
- Reproduction: Windows/Python3.14.0 with requirements.lock, README commands;
  benchmarks fetch official PDFs explicitly with hash checks. Source documents
  are not redistributed without an established license. CI is configured for
  Windows/Python3.14 tests/Ruff; remote execution must be checked separately.
- Agent-assisted implementation, annotations and drafting; historical attribution
  in workstamp.md. [Chat coverage](chat_logs/README.md) states all cutoffs and
  unavailable sources; no claim that active conversations are complete.

## B. Ready-to-send email

Subject: Ur AI take-home submission — Japanese balance-sheet parser

Hi Arun,

Please find my submission in the [GitHub repository](https://github.com/Charitarths-Git/Ur_AI),
with the approach, results and limitations in [REPORT.md](https://github.com/Charitarths-Git/Ur_AI/blob/main/REPORT.md).

The parser extracts born-digital Japanese balance sheets into flat CSV and
hierarchical JSON, retaining raw amounts, comparative periods and parent relationships.
Correctness is measured through ground-truth cell and structural metrics, separate
JSON-tree validation, and accounting checks with an explicit rounding tolerance.

On the supplied human-verified development page, all 43 rows are fully correct and
all 20 evaluable accounting checks pass. I also evaluated five additional official
filing pages using a predeclared issuer split. On the three held-out pages, both
the original and revised parser match 262/262 annotated cells, while the fixed
pdfplumber baseline matches 250/262 and does not infer hierarchy. These additional
annotations are provisional AI drafts, not human-verified ground truth.

The revision fixes dated-footer handling and exposes malformed JSON and suspicious
extractions. Geometry experiments show improved horizontal-noise performance but
also vertical-noise regressions, which the report retains. The main limitation is
the narrow benchmark and its annotation status; broader independently reviewed
pages are needed before claiming generalisation.

[Reproduction instructions](https://github.com/Charitarths-Git/Ur_AI/blob/main/README.md)
and [AI conversation coverage](https://github.com/Charitarths-Git/Ur_AI/blob/main/chat_logs/README.md)
are included. I used AI tools for implementation, review and drafting, with detailed
attribution and export cutoffs documented in the repository.

Thank you for your time and consideration.

Best regards,
Charitarth Singh
