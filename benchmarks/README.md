# Additional-page benchmark and review protocol

This is a small provisional benchmark of five born-digital Japanese balance-sheet
pages from five game/entertainment issuers, not a representative financial-document
sample. Four pages share similar shaded templates. Konami uses an IFRS statement
of financial position and includes liabilities/equity on the selected page; the
others are asset pages. No scanned-page or multi-page assembly claim is made.

## Provenance and split

manifest.json records official URLs, filing dates, one-based PDF pages, million-yen
units, SHA-256 hashes and access/reuse notes. Nintendo/Capcom are development;
Sega Sammy/Square Enix/Konami are held out at issuer level. Split commit f5310c3
predates acquisition. Original parser: 3e14d24. Candidate: 33025ad, frozen before
held-out prediction. No parser tuning followed the benchmark. Future changes
motivated by these failures must reclassify this set as development.

The benchmark runner materializes both parser revisions from Git into ignored
outputs/frozen folders, using the same installed packages. It does not substitute
working-tree parser code. A shallow clone needs both referenced commits fetched.
The evaluator may evolve independently; its schema and report identify the scores.

## Ground truth and review

annotations/*.json were drafted by the coding agent while viewing rendered pages,
before predictions, independently of extraction outputs. They are **AI_DRAFT**,
not independently checked and not human-verified. This is source independence,
not reviewer independence. Raw strings and normalized amounts are retained;
Japanese glyph spacing is treated as typographic, and image-ambiguous nil strokes
are represented by a full-width dash. Exact raw/label metrics therefore depend on
these transcription conventions and must be read with the review caveat.

Depth follows visible indentation. Repeated labels have occurrence identities
assigned in reading order. Headers have empty values. Gross/contra/net groups
follow the printed nested lines; a standalone net-qualified asset amount without
a preceding gross/contra group is annotated line_item. Subtotals are at their
printed indentation. Treasury stock was annotated line_item in this draft; the
parser calls it contra. Konami's final liabilities/equity sum is annotated total,
but the parser calls it subtotal. These ontology choices need human adjudication;
they remain measured disagreements, not silently accepted correct results.

After the first run, enlarged source images confirmed four transcription errors:
Nintendo row19 ソフトウェア → ソフトウエア; Capcom row25 投資有価証券 → 繰延税金資産,
row26 繰延税金資産 → その他; Konami row26 previous16,615 →10,615.
The same agent made these corrections after seeing mismatches, so this review is
not blind or independent. Initial drafts remain in fcce5e0 and initial scores in
eval/results/benchmark_initial_annotations. Revised scoring reused saved extractions
and timing samples; parser code and row-type decisions were unchanged.

To review: run the commands below, compare each JSON annotation row against the
corresponding outputs/benchmark_sources/<issuer>.png, check raw strings, values,
parents/types and nil glyphs, and record reviewer/date/corrections. Leave both
verified_by_human and independently_checked false until those actions occur.
No human review is implied by this deliverable.

## Reproduce

From the repository root in the documented Python environment:

```powershell
$env:PYTHONIOENCODING="utf-8"
python scripts/run_benchmark.py --download --render
```

Downloads are explicit; CI never runs this command. PDFs are issuer-copyright
materials with no redistribution license established, so source PDFs/images are
not committed. Public access is not a redistribution license. Hash mismatch stops
the run rather than substituting a changed document. Images are rendered only for
review; document retrieval/annotation time is outside extraction timings.

If Python's certificate store cannot verify Sega's certificate, use Windows' OS
certificate store with TLS validation still enabled, then rerun the command:

```powershell
Invoke-WebRequest -Uri "https://www.segasammy.co.jp/cms/wp-content/uploads/pdf/ja/ir/20250512_q4_tanshin_j.pdf" -OutFile "outputs/benchmark_sources/sega.pdf"
```

Do not disable certificate verification. `--rescore` reuses existing ignored
outputs/benchmark_runs artifacts and their timing samples after annotation review;
it is not a fresh performance run. Normal runs repeat extraction and timing.

## Baseline and timing

The pdfplumber baseline uses its text/text table strategies, minimum vertical
support3 and horizontal1, and fixed3-point text/snap/join/intersection tolerances.
This deliberately simple default configuration was fixed before held-out runs;
it was not optimized using held-out pages. It receives no parser coordinates,
row tree, predictions or annotations. The largest extracted grid is retained.
The adapter concatenates label cells, uses the last two cells as values, removes
leading nonnumeric grid rows, and applies the shared pure amount normalizer.
Chronology assumes left=previous/right=current; hierarchy and row types are N/A.
This loses leading label-only headers, counted as missing rows, not excluded.

Original/candidate/pdfplumber use the same machine, documents and package versions.
One excluded warmup precedes five runs per page/engine. Timing includes opening
and reading the PDF, extraction, normalization and in-memory serialization;
process/import startup, result-file writes, annotations and evaluation are excluded.
OS file cache is warm. Parser serializes CSV+hierarchical JSON; pdfplumber serializes
CSV+flat records, so structural capability is explicitly unequal. Individual
samples, median, inclusive-quartile IQR and environment are in report.json.
Engine order is fixed, not randomized; small differences are not speedup claims.

## Results

See ../eval/results/benchmark/report.md and report.json for every page, all
failures/warnings, missing/extra rows, cell/label/type/hierarchy/full-row scores,
separate JSON validation, pooled counts and per-page means. Undefined and unsupported
metrics are N/A. GT alignment is the same deterministic label/value DP for every
engine. Repeated indistinguishable rows remain ambiguous; perfect alignment is
not proof of identity. The supplied verified development page is reported separately.
