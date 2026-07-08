# Backtest report

- input: `runs\census_full_20260708\census_full_weekly.ndjson`
- week_count: `53`
- forward_horizon: `12`
- seed: `20260708`

## Rule results

|rule|verdict|n|effect_size|evidence|claim_level|
|---|---|---:|---:|---|---|
|Retention lower-band (4 consecutive weeks)|기각|396016|-0.2445|precision=0.5285, recall=0.0311, risk_diff=-0.2445, p=1.0000, band_q=0.25|L2|
|1500 inflexion with placebo checks|기각|57|-0.1880|effect=-0.1880, p=1.0000, target=1500|L2|
|AirTime and future growth correlation|지지|137886|0.9657|rho=0.0343, p=0.0025, n=137886|L3|
|Segment-axis bottleneck indicator|기각|396016|-0.0830|lift=-0.0830, severity_corr=0.0466, severity_corr_p=0.0025, weak_axes_min=2, axis_q=0.25, n=396016|L2|
|Growth outlook (efficiency x momentum, §6.3.2)|지지|185896|0.4842|green_rate=0.5578, red_rate=0.0736, base=0.2878, green_p=0.0025, red_p=0.0025, n_green=23027, n_red=18513|L3|

## Decision constants

- `RETENTION_BAND_Q=0.25`
- `RETENTION_STREAK=4`
- `RETENTION_RISK_DIFF_MIN=0.05`
- `RETENTION_PVALUE_MAX=0.05`
- `RETENTION_MIN_SIGNALS=8`
- `THRESHOLD_TARGET=1500`
- `THRESHOLD_PLACEBOS=[750, 1000, 2000, 3000]`
- `THRESHOLD_MIN_SIGNALS=8`
- `THRESHOLD_LIFT_MIN=0.1`
- `THRESHOLD_PVALUE_MAX=0.25`
- `AIRTIME_CORR_MAX_ABS=0.2`
- `AIRTIME_CORR_MIN_N=30`
- `AIRTIME_CORR_PVALUE_MAX=0.2`
- `BOTTLENECK_AXIS_Q=0.25`
- `BOTTLENECK_AXIS_WEAK_COUNT_MIN=2`
- `BOTTLENECK_CORR_MAX=-0.25`
- `BOTTLENECK_CORR_PVALUE_MAX=0.3`
- `BOTTLENECK_MIN_SIGNALS=6`
- `BOTTLENECK_LIFT_MIN=0.1`
- `BOTTLENECK_PVALUE_MAX=0.3`
- `GROWTH_OUTLOOK_Q_HIGH=0.75`
- `GROWTH_OUTLOOK_Q_LOW=0.25`
- `GROWTH_OUTLOOK_MOMENTUM_WEEKS=4`
- `GROWTH_OUTLOOK_MIN_SIGNALS=30`
- `GROWTH_OUTLOOK_LIFT_MIN=0.15`
- `GROWTH_OUTLOOK_PVALUE_MAX=0.05`
- `PERMUTATION_ROUNDS=400`
- `MOTION_MEDIAN_WINDOW=4`
- `MISSING_DELTA_FALLBACK=-0.05`
- `MISSING_DELTA_FALLBACK_Q=0.05`
- `FORWARD_HORIZON=12`
- `RANDOM_SEED=20260708`

### Formula/logic changelog
- `_binary_metrics` lift formula: `precision - base_rate` (changed from `recall - base_rate`).
- Retention verdict uses `risk_diff >= RETENTION_RISK_DIFF_MIN` and `pvalue <= RETENTION_PVALUE_MAX`.
- Threshold-delta missing values are replaced by 5th-percentile observed delta (or fallback default if none).
- Missing-outcome sensitivity branch now treats missing outcome as stagnation candidate (`True`).
- `_slope` is relative weekly growth `((end/start)-1)/delta` (changed from absolute delta; segment-pooled comparison needs level-free slopes per trajectory v3 spec).
- Airtime verdict is effect-size-bound only (`abs(rho)<=0.20`); p-value reported as evidence, not required (equivalence claim).

## Claim-level update

- support -> L3 keep
- reject  -> downgrade to L2
- insufficient -> hold