# Tinkaton (great) — expert anchor verification

Blob: `20260612_142213_Tinkaton_great.replay.pkl.gz`  
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
| jellicent_brkp_any | Jellicent | 106.20 atk | 106.2015 | MATCH | GIGATON_HAMMER tier 54 thr 106.1707 under rank-1 opp IVs (re-resolved, current gamemaster) |
| annihilape_brkp_any | Annihilape | 106.58 atk | 106.5839 | MATCH | FAIRY_WIND tier 6 thr 106.4733 under rank-1 opp IVs (re-resolved, current gamemaster) |
| azumarill_blkp_any | Azumarill | 143.03 def | 143.0385 | MATCH | BUBBLE tier 4 thr 142.8860 under rank-1 opp IVs (re-resolved, current gamemaster) |
| medicham_blkp_any | Medicham | 141.66 def + 138 hp | 141.6622 | MATCH | DYNAMIC_PUNCH tier 53 thr 141.6164 under pvpoke-default opp IVs (blob resolution); hp >= 138 achievable at this def floor: yes (max achievable hp 143) |
| corsola_galarian_blkp_any | Corsola (Galarian) | 143.04 def + 140 hp | 143.0385 | MATCH | NIGHT_SHADE tier 38 thr 142.7301 under pvpoke-default opp IVs (blob resolution); hp >= 140 achievable at this def floor: yes (max achievable hp 141) |
| altaria_shadow_blkp_any | Altaria (Shadow) | 143.04 def + 141 hp | 143.0385 | MATCH | FLAMETHROWER tier 80 thr 142.4151 under rank-1 opp IVs (re-resolved, current gamemaster); hp >= 141 achievable at this def floor: yes (max achievable hp 141) |
| shadow_drapion_blkp_any | Drapion (Shadow) | 140.21 def | 140.2170 | MATCH | SLUDGE_BOMB tier 39 thr 139.9186 under rank-1 opp IVs (re-resolved, current gamemaster) |
| shadow_politoed_blkp_any | Politoed (Shadow) | 140.91 def | 140.9112 | MATCH | SURF tier 57 thr 140.4446 under pvpoke-default opp IVs (blob resolution) |
