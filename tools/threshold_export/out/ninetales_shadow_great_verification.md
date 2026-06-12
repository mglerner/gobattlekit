# Ninetales (great) — expert anchor verification

Blob: `20260611_231210_Ninetales_great_shadow.replay.pkl.gz`  
Generated: 2026-06-12 by `export_thresholds.py`

Blob vs current gamemaster: OK: all 4096 blob IV spreads match current gopvpsim stats (max |stat delta| 0.00e+00)

Expert claims are parsed from anchor `description` strings in the
authored thresholds TOML. Re-derived values are minimum achievable
focal stat values (IV-grid quantized) that clear the matching damage
tier, computed two ways: from the blob's embedded resolved anchors
(pvpoke-default opponent IVs) and by minimal re-resolution with
rank-1 opponent IVs (`gopvpsim.breakpoints.bulkpoints/breakpoints`,
current gamemaster). A claim MATCHes if either assumption reproduces
it within ±0.011 (experts quote 2 decimals).

| anchor | opponent | expert | re-derived | verdict | detail |
|---|---|---|---|---|---|
