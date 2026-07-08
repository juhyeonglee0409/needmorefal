# Trajectory report

- input: `runs/backtest_20260708/weekly_series.ndjson`
- level: `16.5`
- week_count: `53`
- seed: `20260708`
- bootstrap_iterations: `1000`

## 1) Track C
- 12w (window=12w, n=27, immature=22, sensitivity=15%): rise=22.2%, flat=51.9%, fall=25.9%
- 12w (window=12w, n=27, immature=22, sensitivity=20%): rise=18.5%, flat=59.3%, fall=22.2%
- 12w (window=12w, n=27, immature=22, sensitivity=25%): rise=14.8%, flat=63.0%, fall=22.2%
- 24w (window=24w, n=16, immature=33, sensitivity=15%): rise=37.5%, flat=25.0%, fall=37.5%
- 24w (window=24w, n=16, immature=33, sensitivity=20%): rise=12.5%, flat=50.0%, fall=37.5%
- 24w (window=24w, n=16, immature=33, sensitivity=25%): rise=12.5%, flat=56.2%, fall=31.2%

## 2) Track A
- eligible channels: `window=12w/24w`, `n=8`
12w (window=12w, n=8): q10=-0.1912, q50=0.0000, q90=0.0940
24w (window=24w, n=8): q10=-0.4474, q50=-0.1071, q90=0.2835
- Track A top10 by RMSE (window=12w/24w, n=8):
- top1 (window=12w/24w): channel_id=6f6f15f9d6abcedd8c78e55cd2910188 t0=24 rmse=0.0758
- top2 (window=12w/24w): channel_id=c60605305243b0234e4cd0d10a675b05 t0=11 rmse=0.1010
- top3 (window=12w/24w): channel_id=82e55f09f2235ac3d23c155bf20877de t0=13 rmse=0.1349
- top4 (window=12w/24w): channel_id=b3faaa462d5ed590e966e7ee8936fa53 t0=11 rmse=0.1976
- top5 (window=12w/24w): channel_id=348542b853d10d1c6a4a5163a9977b52 t0=20 rmse=0.2048
- top6 (window=12w/24w): channel_id=bb8b8ed32e1da10a232835f3c7e9ffd6 t0=11 rmse=0.2570
- top7 (window=12w/24w): channel_id=6ead822eba3002cb7e7948cc0696f35b t0=17 rmse=0.4238
- top8 (window=12w/24w): channel_id=d9bea55de83dd6e9083df921480ef1d5 t0=11 rmse=0.4553

## 3) Track B
- Track B sorted by alpha descending at 12w; channels with overlapping CI have `ci_overlap_previous=True`
- Track B top1 (window=12w): channel_id=82ece76b683398c8d8d5e2add3360f02 alpha=2.392135 alpha_ci=[2.32107, 2.46715] ci_overlap_previous=False t0=13
- Track B top2 (window=12w): channel_id=1bba9dea7f936bdcfe06962bcf0d686a alpha=0.450000 alpha_ci=[0.43067, 0.46462] ci_overlap_previous=False t0=36
- Track B top3 (window=12w): channel_id=f9f5fda096ff44d36127036cd18b0db2 alpha=0.075758 alpha_ci=[0.07242, 0.08984] ci_overlap_previous=False t0=18
- Track B top4 (window=12w): channel_id=9ae6c9253f82bd40ea1ddec9266fe3b8 alpha=0.041667 alpha_ci=[0.03243, 0.04585] ci_overlap_previous=False t0=36
- Track B top5 (window=12w): channel_id=ef4f0b562376c1565f69b52e97804c98 alpha=0.017857 alpha_ci=[0.00975, 0.02067] ci_overlap_previous=False t0=36