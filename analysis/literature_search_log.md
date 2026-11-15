# Literature search log

Searches behind the related-work section and its novelty statement. Earlier searches (2026-11-14,
before the main run) used Crossref, the arXiv API and publisher pages; their individual query strings
were not recorded, which is why this log was started. DBLP returned errors (HTTP 429) and was not used.

## 2026-11-14 (after the extension run)

1. arXiv API, `abs:"coding agent" AND (abs:"mutation" OR abs:"quality gate" OR abs:"coverage")`,
   sorted by submission date, first 40 of 129 results screened by title and abstract.
   Closest hits, all read and cited: 2610.28667 (independent verifier vs. builder's own tests),
   2610.27272 (deterministic replay gate for agent-migrated code). Also screened and judged not a
   controlled gate experiment: 2609.36170 (evidence-bound merge gate, scripted adversaries), 2610.03984,
   2611.16114, 2610.01023, 2610.35297, 2610.13065 (already cited).
2. arXiv API, id lookups 2605.17242 (TDDev) and 2610.02952 (GTDD), suggested in review as close
   neighbours; abstracts read; both cited.
3. PyPI JSON API for the release dates of pytest 8.3.4, coverage 7.6.10 and radon 6.0.1 (bibliography).

## 2026-11-14/15 (publication-status checks)

4. Crossref and OpenReview/iclr.cc, published versions of cited preprints: Dipongkor et al. (ICSME
   2026), Wan et al. (ASE 2026, retitled; formerly the TDDev preprint 2605.17242), CodeT (ICLR 2023),
   Self-Debug (ICLR 2024), ImpossibleBench (ICLR 2026), Banik et al. (AITest 2026); bibliography updated.
   No published version found on Crossref for Konstantinou, Vikram, Sion, Ferenczi, Kato (GTDD),
   Schmalbach or Hagatulah.

## 2026-11-15 (completing query 1)

5. arXiv API, query 1 again, results 41 to 129, screened by title and abstract. Closest hits, read:
   2606.17099 (Schmalbach: delegation contracts, hidden acceptance tests, all runs correct; cited),
   2610.33343 (Hagatulah et al.: metric-guided agentic refactoring, paired experiment; cited),
   2608.18645 (CodeHealth vs LLM test effectiveness; not a gate experiment). Also judged not a
   controlled gate experiment with an independent oracle: 2607.08983, 2606.22678, 2604.00280,
   2605.21810, 2606.05570, 2603.08806, 2604.01442, 2605.09573, 2409.10737, 2406.12952 (cited).
   Crossref title searches for 2606.17099 and 2610.33343 found no published versions.

## 2026-11-15 (2026 proceedings through Crossref)

6. DBLP search API: blocked by bot protection (Anubis); not used.
7. Crossref works API, filter `from-pub-date:2026-01-01,type:proceedings-article`, first 40 hits each of
   (a) "coding agents tests quality gates mutation coverage" and (b) "agent-written tests code review
   replace human review LLM agents". Closest hits: Shaw and Beheshti, "Complexity Backpressure for AI
   Coding Agents" (IEEE SSE 2026, 10.1109/SSE72781.2026.00047) and "Wily: High-Performance Complexity
   Gated-Feedback for AI Coding Agents" (ACM CAIS 2026, 10.1145/3786335.3813220); abstracts read via the
   Semantic Scholar API; both cited. Screened by title and judged not a controlled gate experiment with
   an independent oracle: MSR 2026 studies of agent-written tests (10.1145/3793302.3793362,
   10.1145/3793302.3793620), Debug2Fix (ASE 2026), SecMutBench, GEM (CIbSE 2026), and an iterative
   static-analysis loop (CIACON 2026).

Limitation: Crossref keyword search is not a full listing of the ICSE/FSE/ASE/ISSTA 2026 proceedings;
DBLP was unreachable.
