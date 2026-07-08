# Trajectory validation report

- input: `runs/backtest_20260708/weekly_series.ndjson`
- week_count: `53`
- levels: `10.0, 17.0, 30.0, 60.0, 120.0`

|level|track|window|verdict|n|n_first|n_second|value|
|---|---|---|---|---:|---:|---:|---|
|10.0|Track C|12w|stable|49|11|38|rise 27.3% (first) / 28.9% (second), flat 54.5% (first) / 55.3% (second), fall 18.2% (first) / 15.8% (second), diff={'rise': 0.01674641148325362, 'flat': 0.0071770334928230595, 'fall': 0.02392344497607657}
|10.0|Track A|12w|stable|25|25|25|coverage 72.0% vs nominal 80.0% (inside=18)
|120.0|Track C|12w|stable|27|9|18|rise 33.3% (first) / 33.3% (second), flat 33.3% (first) / 38.9% (second), fall 33.3% (first) / 27.8% (second), diff={'rise': 0.0, 'flat': 0.05555555555555558, 'fall': 0.055555555555555525}
|120.0|Track A|12w|unstable|6|6|6|coverage 33.3% vs nominal 80.0% (inside=2)
|17.0|Track C|12w|unstable|23|10|13|rise 10.0% (first) / 30.8% (second), flat 70.0% (first) / 46.2% (second), fall 20.0% (first) / 23.1% (second), diff={'rise': 0.2076923076923077, 'flat': 0.2384615384615384, 'fall': 0.03076923076923077}
|17.0|Track A|12w|unstable|8|8|8|coverage 50.0% vs nominal 80.0% (inside=4)
|30.0|Track C|12w|unstable|18|9|9|rise 44.4% (first) / 22.2% (second), flat 33.3% (first) / 55.6% (second), fall 22.2% (first) / 22.2% (second), diff={'rise': 0.2222222222222222, 'flat': 0.22222222222222227, 'fall': 0.0}
|30.0|Track A|12w|unstable|4|4|4|coverage 25.0% vs nominal 80.0% (inside=1)
|60.0|Track C|12w|unstable|25|10|15|rise 30.0% (first) / 40.0% (second), flat 30.0% (first) / 53.3% (second), fall 40.0% (first) / 6.7% (second), diff={'rise': 0.10000000000000003, 'flat': 0.23333333333333334, 'fall': 0.33333333333333337}
|60.0|Track A|12w|unstable|7|7|7|coverage 100.0% vs nominal 80.0% (inside=7)