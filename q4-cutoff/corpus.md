# Corpus plan

Cutoffs: 1900 first, then 1880, 1905, 1915. Each cutoff gets its own audited corpus and its own
tokenizer. Token counts below are English, before quality filtering, at 4.34 chars/token (32k BPE
trained on 1B chars of pre-1900 text, measured on a held-out shard). Check: the same ratio puts
GPT-1900's 56.4 GB corpus at 21B tokens (1.34B chars in its 0.83 GB shard 5); its card says 22B.

## Sources

| Source | Pre-1900 size | Date provenance | Date reliability | Licence |
|---|---|---|---|---|
| Institutional Books 1.0 (Harvard/IDI, HF `institutional/institutional-books-hl`) | 484.6k dated pre-1900 volumes of 1.08M; English 47% of collection; 246k tokens/volume → **~56B tokens** | MARC 21 `date1`/`date2`/`date_types` | Good for monographs. 32% of volumes undated. Serials carry run spans, not issue dates. Reprints carry the reprint year only when cataloguers recorded it | IDI Early-Access terms: noncommercial, no redistribution, commercial actors (incl. model training) must contact IDI first. Gated on HF |
| AmericanStories (`dell-research-harvard/AmericanStories`) | 155 GB compressed pre-1900 (1774–1899); measured 0.91 article chars per compressed byte → 141B chars → **~32B tokens**, ~24B legible (74% of chars in the sample are classed legible) | Issue date from Library of Congress Chronicling America | Best of the four: dated to the day by issue | CC-BY-4.0 (scans public domain) |
| British Library books (`TheBritishLibrary/blbooks`) | `1800_1899` config: 30.1 GB text, 13.8M pages, all languages → **≤7B tokens** | Catalogue date, ranges collapsed to their mean (`date`), original in `raw_date` | Weak: a range such as 1898–1909 becomes 1903; serial reports list later years in titles | CC0 / Public Domain Mark |
| HathiTrust public domain | Overlaps Institutional Books (Harvard's Google scans are in HathiTrust) | MARC, same as IB | Same as IB | Full text needs an HTRC dataset request; not a download |
| Project Gutenberg | ~75k e-texts, few B tokens, most post-1800 | None per text; author dates only | Bad: modern editions, transcriber notes, introductions, licence header written after 1971 | Public domain in US, Gutenberg trademark text attached |

Cutoff coverage for the later cutoffs (AmericanStories compressed GB / IB dated volumes):
1880: 68 GB / 289k (~47B raw tokens, ~25B after filters). 1905: 185 GB / ~550k. 1915: 254 GB / ~649k. IB volume counts for 1905 and
1915 interpolate the 1900s and 1910s decades evenly.

## Pick

**AmericanStories + Institutional Books, English only, British Library books as a CC0 supplement
with range-aware dating.** Same three sources as GPT-1900, so results compare directly, with
stricter dating and an audit GPT-1900 lacks. Gutenberg is out of the training set.

~90B raw tokens before cutoff 1900; ~40–50B after quality and leak filters (GPT-1900 kept 22B
from the same sources). That covers Chinchilla for a 1B model (20B) and 3B at ~15 tokens/param.

Blocker: the Institutional Books terms require contacting its publisher before training by a
commercial actor. AmericanStories + BL (~25–30B before filters) carry the 1B runs without it.

## Dating rules

1. Document year = the **latest** year in any date field (`date1`, `date2`, `raw_date` range end,
   issue date). Not the mean.
2. Drop undated volumes. Drop MARC date types for continuing resources (`c`, `d`, `u`) and
   reprints (`r`: date1 is the reprint year, keep only if date1 < cutoff).
3. Drop documents whose title holds a year ≥ cutoff.

## Leak audit

Three layers. Each runs per cutoff; the report goes in `audit/<cutoff>/`.

**1. Metadata.** Apply the dating rules; log every drop with its reason. Sample 200 kept volumes
per source and date them by hand from the title page scan text.

**2. Text canaries.** One pass over every document, lowercased, substring prefilter then regex
(`pilot/prep_and_scan.py`, 1.34B chars in ~10 min on one core).

- Strong (coined or given their physics sense after 1900; any hit drops the document and goes to
  review): photon, space-time, quantum of action, Planck's constant, theory of relativity,
  special/general relativity, Lorentz transformation, quantum mechanics/theory, isotope,
  transistor, Einstein, Heisenberg, Schrödinger. Per cutoff, add the terms and names that entered
  print after it (for 1880: electron, Hertzian waves, X-rays, radioactivity, Michelson–Morley).
- Contextual (words with a pre-1900 sense; a hit counts only with a context rule): Titanic (with
  ship, iceberg, sank), Bohr (with atom, Niels), proton/neutron (with nucleus, electron), World War,
  League of Nations, Bolshevik, Wright brothers (with aeroplane, Kitty Hawk), television. The
  pilot scan below shows why: every bare-word hit on these was a pre-1900 use.
- Weak (legitimate before 1900, rising after; tracked as frequency per million words per year,
  never filtered by itself): quantum/quanta, relativity, electron, radioactivity, X-rays, ether,
  Michelson, Lorentz, Planck. A jump in the last years before the cutoff flags misdated text.
- Year references: count 4-digit years ≥ cutoff. OCR turns train times and prices into such
  numbers ("1906 a. m." in an 1899 timetable), so the rule is ≥5 distinct years in running prose,
  not in tables.

**3. Reprints and front matter.** Reprints keep the old date and add a modern preface or notes.

- Scan the first and last 5% of each volume with a lower threshold (one strong canary, one year ≥
  cutoff, or "copyright 19xx", "edition of 19xx", "reprinted", "with an introduction by",
  Roman numeral years MCM–).
- MinHash every pre-cutoff volume against post-cutoff volumes of the same source. A near-duplicate
  whose extra text falls in front or back matter marks a reprint; drop the extra pages.
- Date classifier: a character n-gram model trained on issue-dated AmericanStories text predicts
  a decade per document. Flag documents predicted ≥ cutoff+10 for review. This catches OCR-era
  metadata errors (wrong century, wrong volume record).

**Calibration.** Plant 1,000 synthetic leak documents (modern physics paragraphs, post-cutoff
prefaces, misdated serials) into a copy of the corpus before filtering; report the fraction each
layer catches. Target: ≥99% of planted strong-canary documents, ≥90% of planted prefaces.

**Model-side check.** After pretraining, compare per-token loss on 500 post-cutoff sentences
(dated facts, coinages) against 500 length-matched pre-cutoff sentences, for our model and for a
same-size model trained on a held-out shuffled-date control. A post-cutoff loss gap smaller than
the control's flags leakage.

## Pilot audit of GPT-1900's corpus

Canary scan of `mhla/pre1900-corpus` shard 5 (1 of 6 shards). Results in
`pilot/scan_shard5.json`; summary below.

50,000 documents, 1.34B chars, years 1663–1899 (48,043 AmericanStories articles, 1,957
Institutional Books volumes).

| Check | Hits | Verdict |
|---|---|---|
| ≥5 years 1900–1999 | 0 | GPT-1900's own date filter already removed these |
| Strong canaries | Titanic 112, proton 2, Bohr 2, League of Nations 1, World War 1 | All 8 sampled hits (≤3 per term) are pre-1900 uses: "Titanic strength", the 1872 "Proton outrage", German *Bohrer*, an 1886 history of a "League of Nations", OCR noise "world war TUX" |
| Weak canaries | ether 914, quantum/quanta 231, aether 72, relativity 17, Planck 16, X-rays 10, Lorentz 8, electron(s) 3, Michelson 3 | Tracked, not filtered |

Two findings. No residual leak shows in this shard; the scan measures what survived GPT-1900's
filters, not what they removed, and this shard is 96% newspaper articles. And bare-word canaries are mostly false
positives in period text, hence the contextual tier above. Proper names that predate the
cutoff (Planck, Lorentz, Michelson, all publishing before 1900) stay weak canaries.
