# CHZZK Streamer Channel Diagnosis — Advisor Review Request (Part 1)

**Case:** Anonymous CHZZK streamer (general game + virtual hybrid, ~700 followers)
**Analysis period:** 2024 Q1 – 2026 Q2 (585 broadcast sessions)
**Core cohort:** 323 channels (T1=184, T2=196, overlap=57)
**Date:** 2026-06-17 v2
**Prepared by:** Streamer Consulting Project

---

## §1. What This Analysis Claims

**Domain context:** CHZZK is South Korea's primary live-streaming platform, launched in late 2023 as Naver's successor to its previous streaming service. The general-game category contains several thousand active channels. A channel with ~700 followers and a peak of 20 concurrent viewers sits in the lower-mid tier — comparable to a small independent content creator building an audience from the ground up.

**In one paragraph:** This channel has grown steadily over two years (avg viewers +57%, peak +50%, chat engagement +201%). Within its peer cohort, it ranks in the upper-mid range for audience scale (71st percentile) but broadcasts at the absolute maximum volume (112h/month, 100th percentile). There is a weak negative correlation between broadcast hours and viewer output across the peer band (r = −0.315), suggesting that more volume may not translate to more audience. The central recommendation is to test broadcast intensity optimization rather than continue adding volume.

**Three claims that need your scrutiny:**

1. **The cohort is the right comparison set.** We used peak-based filtering (peak_recent_median 12–45) across two categories (general game + virtual) to build a dual-category cohort of 323 channels. This is a design choice with trade-offs.

2. **Efficiency is average, not above average.** Raw efficiency percentile (59.8%) overstates true efficiency due to a size effect. After log-log regression adjustment, the subject sits near the regression line.

3. **Broadcast volume has diminishing returns.** The negative correlation (r = −0.315) between hours and viewership is cross-sectional and could reflect reverse causality. We use it to recommend intensity optimization, not volume reduction.

---

## §2. What I Need You to Review

**Estimated review time: 60–90 minutes.** If time is limited, Q1 and Q6 are highest priority.

**For each question, I'm asking: "What would you do differently?" — not "Is this OK?"**

| # | Question | What's at stake |
|---|---|---|
| Q1 | If you received this hybrid general-game/virtual streamer case, **what would be the first thing you'd change** about the cohort design (dual-category, peak-filtered, n=323)? | If the cohort is wrong, all percentiles and peer comparisons are wrong. |
| Q2 | We excluded sessions ≥14h as outliers (603 sessions, 2.5%). **If you were designing the exclusion rule, what method would you use?** Would you apply a fixed cutoff, IQR-based per-channel detection, or something else? | The exclusion affects the broadcast-volume analysis (§6, Q6) directly. |
| Q3 | For goal-range estimation we use observed band medians (primary) supplemented by regression extrapolation (R²~0.38). **At what R² would you stop using regression and switch to a different method?** | Goal-range estimates feed the client-facing growth roadmap. Overconfident ranges mislead. |
| Q4 | The subject's percentile drops from 71.7% (T1 general game) to 44.9% (T2 virtual), a 27pp gap. We attribute this to T2 channels being larger (median follower 1,150 vs 744). **Would you normalize, or is the raw gap the correct signal?** | Determines whether the subject is "upper-mid" or "mid" depending on the reference frame. |
| Q5 | Retention (avg/peak = 0.712, 86th percentile) is presented as a strength, but roughly half of it comes from the peak being −15% below regression prediction rather than the average being high. **How would you frame this to the client?** | The client currently believes retention is a confirmed strength. If it's partly an artifact of weak peak, the narrative changes. |
| Q6 | The negative correlation between broadcast hours and viewership (r = −0.315, n=197) is our central actionable finding. **What would be the first analysis you'd run to separate selection effect from causal effect?** | If it's selection (low-audience streamers compensate with more hours), the recommendation reverses from "optimize intensity" to "investigate why audience is low." |

**Deliverable format:** For each Q, I'd find most useful: (a) your alternative approach, (b) severity of the issue (blocks conclusion / weakens it / cosmetic), (c) one sentence on what you'd tell the client differently. Beyond Q1–Q6, any additional observations are welcome.

---

## §3. Method Decision Log

These are the key design choices I made and the alternatives I considered. This is where I'm most uncertain and where your expertise matters most.

| Decision | Chosen | Rejected alternative | Why I chose this | What I'm unsure about |
|---|---|---|---|---|
| Cohort filter metric | peak_recent_median 12–45 | follower-based (e.g. 300–2000) | Follower counts include inactive/inflated accounts. Peak reflects actual concurrent audience and is less susceptible to dormant-follower noise. | Whether the 12–45 window is too narrow or too wide. No sensitivity table across windows yet. |
| Dual-category design | T1 (general game) + T2 (virtual) as separate cohorts with overlap tracked | Single merged cohort | Subject operates in both categories. Merging would hide the population composition difference (T2 is larger on average). | Whether the T1/T2 split creates more confusion than clarity for the advisor and client. |
| Efficiency metric | peak/follower | avg/follower, viewership/follower | Peak is less affected by broadcast length than avg. Viewership/follower bakes in broadcast hours and conflates volume with efficiency. | Whether peak/follower is standard in this domain or idiosyncratic to our framework. |
| Outlier exclusion | Fixed 14h per session | IQR-based per-channel cutoff, no exclusion | 14h+ sessions are overwhelmingly overnight unattended streams in this genre. A fixed cutoff is simpler and more transparent. | Whether per-channel IQR would change conclusions materially. IQR-based detection is listed in our tooling but was not applied in this version. |
| Regression model | log-log (efficiency ~ follower) | Linear, polynomial, quantile | The efficiency-follower relationship follows a power law in scatter inspection. Log-log linearizes this cleanly (R² = 0.788). | Forward regressions (peak ~ follower, avg ~ follower) have R² ~ 0.38. These are used as supplementary estimates only, not primary. |
| Broadcast-volume finding | Presented as "single most actionable finding" | Presented as "observed pattern, further testing needed" | The r = −0.315 is consistent across the peer band and the subject is at the extreme. Practical relevance seemed high. | Whether "most actionable" overstates confidence given cross-sectional data and unresolved causality direction. |

---

## §4. Evidence: Cohort Design and Data

### 4.1 Cohort Structure

| Pool | n | Purpose | Used in |
|---|---:|---|---|
| T1 (main) | 184 | Primary benchmark: CHZZK general game, peak 12–45 | Percentiles, regression, positioning |
| T2 (aux) | 196 | Virtual benchmark: CHZZK virtual, peak 12–45 | Cross-cohort robustness, T1↔T2 gap |
| Overlap | 57 | Channels in both T1 and T2 | Hybrid subgroup analysis |
| Core unique | 323 | T1 ∪ T2 (deduplicated) | Primary analytical universe |
| Upper band (ref) | 271 | Followers 3K–10K, multi-category, peak 12–45 | Growth projections beyond current tier |
| Enrichment-only | 266 | Profile data only, no broadcast records | Profile enrichment denominator |
| Total profiled | 860 | All channels with profile data | Profile-level summaries only |
| Broadcast-record pool | 309 channels / 24,056 sessions | Channels with broadcast data collected | Broadcast-level analyses (retention, volume, etc.) |

**Note:** The "860" figure refers to the total profiled universe (323 + 271 + 266), not the analytical cohort. Core analyses use the 323-channel cohort or the 309-channel broadcast pool. Growth projections reference the 271-channel upper band. The enrichment-only channels contribute profile context but do not appear in any percentile, regression, or comparative analysis.

### 4.2 Data Collection

| Item | Detail |
|---|---|
| Broadcast records | 309 channels, 24,056 sessions |
| Outlier exclusion | Sessions ≥14h removed: 603 sessions (2.5%). Fixed threshold applied uniformly. IQR-based detection was available in our pipeline but not applied in this version — see Method Decision Log §3. |
| Subject data | 585 sessions (2024.02–2026.06), 226 daily stats |
| Collection tool | Softcon viewership platform (automated browser collection) |
| Success rate | 95.7% (14 channels failed) |
| Profile enrichment | 965/965 channels via Softcon + CHZZK API |

### 4.3 Known Collection Limitations

**Failed channels:** 14 channels (4.3%) failed during automated collection. These channels had a lower median peak (14) compared to successful channels (18), introducing a possible small-channel underrepresentation. We cannot fully rule out that this biases cohort percentiles upward. A failed-channel sensitivity analysis (excluding vs. imputing the 14 channels) has not yet been performed.

**Temporal mismatch:** Cohort broadcast records cover 2026 Q1–Q2 only. The subject has data from 2024 Q1. Long-term growth-rate comparisons between subject and cohort are therefore not possible — we compare current-state positioning only.

---

## §5. Evidence: Statistical Methods

### 5.1 Multi-axis Positioning

| Axis | Metric | Subject | T1 %ile | Interpretation |
|---|---|---:|---:|---|
| Audience scale | peak_recent_median | 20 | 71.7% | Upper-mid |
| Follower class | follower count | 711 | 32.6% | Lower-mid |
| Efficiency | peak/follower | 2.8% | 59.8% | Near average after size adjustment (see below) |
| Activity volume | monthly hours | 112h | 100% | Maximum — this is an exposure axis, not a performance axis |

**Efficiency size adjustment:** Raw efficiency percentile (59.8%) includes a structural size effect — smaller channels naturally show higher peak/follower ratios. The log-log regression residual is −0.039 in log-space, placing the subject near the regression line. This means efficiency is approximately average for a channel at this follower level, not above average.

**Activity volume note:** The 100th percentile on monthly hours should not be read as a strength. In the context of this analysis, extreme broadcast volume is an exposure/risk indicator (see §6.3).

**Metric definitions:**

| Metric | Definition | Window |
|---|---|---|
| monthly hours (112h) | Mean of quarterly total hours / 3, averaged over the most recent available quarters. Not a calendar 30-day sum. | Rolling quarterly average |
| retention (0.712) | Mean of quarterly [median(avg_viewers) / median(peak_viewers)], computed over 2026 Q1–Q2. Not a per-session median ratio. | 2026 Q1–Q2 |
| peak_recent_median (20) | Median of per-session peak viewers over the most recent quarter. | Most recent quarter |

### 5.2 Log-log Regression

| Cohort | Model | Slope | R² | p-value | n |
|---|---|---:|---:|---|---:|
| T1 | log(eff) ~ log(follower) | −0.804 | 0.788 | 3.9e-63 | 184 |
| T2 | log(eff) ~ log(follower) | −0.766 | 0.749 | 1.4e-59 | 196 |

**Interpretation:** A 10× increase in followers corresponds to efficiency dropping to approximately 0.16×. This diminishing-returns curve is referenced in the class upgrade cost framework (Part 2, §6.1, not included in this review packet).

**Missing metadata (to be provided on request):** Standard errors, 95% confidence intervals for slope, adjusted R², residual diagnostics (Q-Q plot, Shapiro-Wilk), Cook's distance for influential points. These are available in our pipeline output but are not reproduced here for brevity. If any of these would change your assessment, I can provide them.

**Forward regressions** for goal-range estimation: log(peak) ~ log(follower) R²=0.39, log(avg) ~ log(follower) R²=0.37. These have substantially lower explanatory power and are used only as supplementary range estimates alongside observed band medians.

**Note on Q3:** The goal-range estimates themselves (Part 2, §6.2) are not included in this review packet. Q3 asks about the principle of using dual methods (band medians + regression), not about specific goal numbers.

### 5.3 Robustness Checks

| Test | Pool | n | Subject %ile | Note |
|---|---|---:|---:|---|
| R1 baseline | T1 recent_median | 184 | 71.7% | Primary reference |
| R2 wider pool | T1 all_median | 230 | 80.4% | Wider pool inflates rank |
| R4 peak p95 | T1 p95 | 188 | 76.1% | Stable |
| R5 T2 virtual | T2 | 196 | 44.9% | Population composition effect |
| R7 excl. marathon | T1 minus marathon | 166 | 73.5% | Stable |

**Within T1**, subject percentile is stable at 71–76% (±5pp) regardless of pool variant. This is a genuine stability signal.

**T1 vs T2 gap** (71.7% → 44.9%, Δ27pp) reflects population composition: T2 virtual channels are larger on average (median follower 1,150 vs 744). This is a descriptive observation, not a normalized cross-cohort comparison. Follower-adjusted percentiles have not been computed.

### 5.4 Retention

Subject retention (avg/peak) = 0.712, placing at the 86th percentile in T1. However, this is a mixed signal:

- The subject's **avg** is on the regression line (as expected for this follower level)
- The subject's **peak** is −15% below regression prediction

Roughly half the retention strength comes from avg being normal while peak is slightly depressed. This means retention should be presented as **"stable average viewership combined with below-expected peak"** rather than as a confirmed strength in isolation.

---

## §6. Evidence: Key Quantitative Findings

### 6.1 Growth Trajectory

| Metric | 2024 Q1 | 2026 Q2 | Change |
|---|---:|---:|---|
| avg_median | 10.6 | 16.6 | +57% |
| peak_median | 16 | 24 | +50% |
| follower | 471 | 711 | +51% |
| chat_median | 448* | 1,350 | +201% |

*Chat baseline is 2024 Q2 (Q1 data unavailable).

All metrics show concurrent growth. Avg growth (+57%) slightly outpaces peak and follower growth (+50–51%), which is consistent with improving viewer retention over time — though this inference is based on trend direction only, not a direct retention time-series.

A notable dip occurred in 2025 Q1 (peak 20→16, −20%) followed by recovery and acceleration into 2026.

### 6.2 Peer Comparison

| Group (follower 500–1500) | n | avg median | avg≥14 rate |
|---|---:|---:|---:|
| General game only | 84 | 8 | 14% |
| Hybrid (overlap) | 37 | 13 | 41% |
| Virtual only | 76 | 14 | 54% |
| **Subject** | 1 | **14** | — |

In this raw within-band comparison, hybrid channels show a higher median avg (13) than general-game-only channels (8). The subject performs at the hybrid group median. However, this comparison is not adjusted for follower distribution, broadcast volume, or survivorship within each group. The difference may partly reflect category composition rather than a pure hybrid advantage.

### 6.3 Broadcast Volume

Across the peer band (follower 500–1500, n=197): Pearson r = −0.315 between monthly broadcast hours and avg_median (p < 0.001).

The subject broadcasts 112h/month (100th percentile in the cohort) but achieves approximately 1.3× the cohort median output. The negative correlation suggests diminishing or possibly adverse returns to broadcast volume at the margin.

**What this finding supports:** Testing whether marginal hours contribute to audience growth before adding more volume. Specifically, analyzing output per hour in different time slots and session lengths.

**What this finding does not support:** A causal claim that reducing hours will increase viewership, or a blanket recommendation against current broadcast volume. The correlation is cross-sectional and could reflect a selection effect (lower-audience streamers compensating with more hours).

**Figure note:** If a scatter plot accompanies this section, dots are anonymized/jittered for privacy. The r, n, and p values are computed from the actual peer dataset, not from the visualization.

---

## §7. Consolidated Limitations

1. Peak 12–45 window excludes sub-12 micro-streamers and 45+ mid-tier channels. Growth projections beyond ~5,000 followers rely on upper-band reference data (n=271), not the core cohort.
2. 14 failed channels (4.3%) skew smaller, possibly inflating cohort percentiles. Sensitivity analysis pending.
3. Cohort broadcast records cover 2026 Q1–Q2 only. No longitudinal growth-rate comparison with cohort.
4. Forward regressions (R² ~ 0.38) are weak. Used as supplementary estimates only.
5. T1↔T2 percentile comparison is raw (not follower-adjusted).
6. Retention is a mixed signal (avg normal + peak depressed), not a pure strength.
7. Broadcast-volume correlation is cross-sectional. Causality direction unresolved.
8. Peer comparison (§6.2) is not adjusted for within-group distribution differences.
9. Regression table does not include SE, CI, or residual diagnostics in this version.

---

## Appendix A: Pool Dictionary

| Pool name | n | Source | Filter | Role in analysis |
|---|---:|---|---|---|
| T1 main | 184 | CHZZK general game | peak_recent_median 12–45 | Primary cohort: percentiles, regression, positioning |
| T2 aux | 196 | CHZZK virtual | peak_recent_median 12–45 | Cross-cohort robustness, virtual dimension |
| Overlap | 57 | T1 ∩ T2 | — | Hybrid subgroup |
| Core unique | 323 | T1 ∪ T2 | — | Analytical universe |
| Upper band | 271 | Multi-category | fol 3K–10K, peak 12–45 | Growth projection reference |
| Enrichment-only | 266 | Various | Profile match only | Profile context; not in any analytical output |
| Total profiled | 860 | All above | — | Profile-level universe. Not an analytical cohort. |
| Broadcast pool | 309 ch / 24,056 sess | Subset with broadcast data | Collection success | Broadcast-level analyses |
| Subject | 1 ch / 585 sess | Target channel | 2024.02–2026.06 | Diagnosis target |

## Appendix B: Metric Definitions

| Metric | Formula | Window | Note |
|---|---|---|---|
| peak_recent_median | median(per-session peak viewers) | Most recent quarter | Cohort filter and audience scale axis |
| avg_median | median(per-session avg viewers) | Per quarter | Growth trajectory metric |
| follower | Absolute follower count (from daily stats, not broadcast CSV) | Snapshot | Broadcast CSV contains per-session delta only |
| retention | mean of quarterly [median(avg) / median(peak)] | 2026 Q1–Q2 | Not a per-session ratio |
| efficiency | peak_recent_median / follower | At analysis date | Raw metric; size-adjusted via regression residual |
| monthly hours | quarterly total hours / 3, averaged over recent quarters | Rolling quarterly | Not a calendar 30-day window |
| viewership | avg_median × monthly hours | Derived | Volume-weighted output; bakes in broadcast hours |

---

**v1 → v2 Change Log**

| Change | Rationale |
|---|---|
| Added §1 Executive Summary with domain context | Advisor needs scale context for CHZZK and the 700-follower tier |
| Restructured: conclusions first, then evidence by topic | Advisor can now read §1–§2 (5 min) and selectively dive into evidence |
| Added §3 Method Decision Log | Shows rejected alternatives — the most useful input for expert review |
| Reframed Q1–Q6 as "what would you change" | Elicits expert alternatives rather than yes/no validation |
| Added deliverable format guidance for reviewer | Structures advisor output for downstream action |
| Fixed pool 860 definition (P-01) | §2.1 and Appendix now consistent; pool dictionary added |
| Clarified outlier method (P-02) | 14h fixed, IQR available but not applied; relationship explicit |
| Softened selection bias language (P-03) | "no bias detected" → "cannot fully rule out" |
| Fixed "exactly average for 500-follower" (P-05) | → "approximately average for a channel at this follower level" |
| Softened hybrid advantage (P-10) | "clear" → "observed in raw within-band comparison" |
| Softened broadcast-volume recommendation (P-11) | Separated "what the finding supports" from "what it does not support" |
| Added figure evidence note (P-12) | Anonymized dots vs. actual statistics distinguished |
| Added metric definitions (P-20) | monthly hours 112h, retention 0.712 window definitions explicit |
| Added §7 Consolidated Limitations | Previously scattered across sections; now one scannable list |
| Regression metadata note (P-07) | SE/CI/diagnostics available on request; gap acknowledged |
| Activity volume reframed as exposure axis (P-13) | 100th percentile not presented as strength |

---

*End of Part 1 review packet. Part 2 (§6 goal-range estimation, §7 content analysis, §8 action plan) to follow separately.*
