# Trajectory report

- input: `runs/backtest_20260708/weekly_series.ndjson`
- level: `16.7`
- week_count: `53`
- seed: `20260708`
- bootstrap_iterations: `1000`

## 1) Track C
- 12w (window=12w, n=25, immature=17, sensitivity=15%): rise=28.0%, flat=48.0%, fall=24.0%
- 12w (window=12w, n=25, immature=17, sensitivity=20%): rise=24.0%, flat=56.0%, fall=20.0%
- 12w (window=12w, n=25, immature=17, sensitivity=25%): rise=20.0%, flat=60.0%, fall=20.0%
- 24w (window=24w, n=14, immature=28, sensitivity=15%): rise=35.7%, flat=28.6%, fall=35.7%
- 24w (window=24w, n=14, immature=28, sensitivity=20%): rise=7.1%, flat=57.1%, fall=35.7%
- 24w (window=24w, n=14, immature=28, sensitivity=25%): rise=7.1%, flat=64.3%, fall=28.6%

## 2) Track A
- eligible channels: `window=12w/24w`, `n=6`
12w (window=12w, n=6): q10=-0.2778, q50=0.0000, q90=0.0789
24w (window=24w, n=6): q10=-0.4540, q50=-0.1071, q90=0.1716
- Track A top10 by RMSE (window=12w/24w, n=6):
- top1 (window=12w/24w): channel_id=6f6f15f9d6abcedd8c78e55cd2910188 t0=24 rmse=0.0758
- top2 (window=12w/24w): channel_id=82e55f09f2235ac3d23c155bf20877de t0=13 rmse=0.1349
- top3 (window=12w/24w): channel_id=b3faaa462d5ed590e966e7ee8936fa53 t0=11 rmse=0.1976
- top4 (window=12w/24w): channel_id=348542b853d10d1c6a4a5163a9977b52 t0=21 rmse=0.2005
- top5 (window=12w/24w): channel_id=bb8b8ed32e1da10a232835f3c7e9ffd6 t0=11 rmse=0.2570
- top6 (window=12w/24w): channel_id=6ead822eba3002cb7e7948cc0696f35b t0=17 rmse=0.4238

## 3) Track B
- Track B sorted by alpha descending at 12w; channels with overlapping CI have `ci_overlap_previous=True`
- Track B top1 (window=12w): channel_id=82ece76b683398c8d8d5e2add3360f02 alpha=2.392135 alpha_ci=[2.32107, 2.46715] ci_overlap_previous=False t0=13
- Track B top2 (window=12w): channel_id=1bba9dea7f936bdcfe06962bcf0d686a alpha=0.552083 alpha_ci=[0.53228, 0.57120] ci_overlap_previous=False t0=37
- Track B top3 (window=12w): channel_id=f9f5fda096ff44d36127036cd18b0db2 alpha=0.075758 alpha_ci=[0.07242, 0.08984] ci_overlap_previous=False t0=18
- Track B top4 (window=12w): channel_id=d9bea55de83dd6e9083df921480ef1d5 alpha=0.052632 alpha_ci=[0.04511, 0.05517] ci_overlap_previous=False t0=29
- Track B top5 (window=12w): channel_id=9ae6c9253f82bd40ea1ddec9266fe3b8 alpha=0.041667 alpha_ci=[0.03243, 0.04585] ci_overlap_previous=True t0=36
- Track B top6 (window=12w): channel_id=ef4f0b562376c1565f69b52e97804c98 alpha=0.017857 alpha_ci=[0.00975, 0.02067] ci_overlap_previous=False t0=36