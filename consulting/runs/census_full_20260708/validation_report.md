# Trajectory validation report

- input: `runs/census_full_20260708/census_full_weekly.ndjson`
- week_count: `53`
- levels: `10.0, 17.0, 30.0, 60.0, 120.0`

|level|track|window|verdict|n|n_first|n_second|value|
|---|---|---|---|---:|---:|---:|---|
|10.0|Track C|12w|unstable|561|209|352|rise 15.3% (first) / 25.9% (second), flat 49.3% (first) / 52.8% (second), fall 35.4% (first) / 21.3% (second), diff={'rise': 0.10541267942583735, 'flat': 0.03558612440191389, 'fall': 0.1409988038277512}
|10.0|Track A|12w|stable|250|250|250|coverage 75.2% vs nominal 80.0% (inside=188)
|120.0|Track C|12w|stable|49|17|32|rise 29.4% (first) / 28.1% (second), flat 35.3% (first) / 43.8% (second), fall 35.3% (first) / 28.1% (second), diff={'rise': 0.01286764705882354, 'flat': 0.08455882352941174, 'fall': 0.07169117647058826}
|120.0|Track A|12w|unstable|13|13|13|coverage 53.8% vs nominal 80.0% (inside=7)
|17.0|Track C|12w|stable|306|129|177|rise 24.0% (first) / 31.1% (second), flat 51.2% (first) / 48.6% (second), fall 24.8% (first) / 20.3% (second), diff={'rise': 0.07042438575745633, 'flat': 0.025752200762054922, 'fall': 0.044672184995401376}
|17.0|Track A|12w|stable|126|126|126|coverage 74.6% vs nominal 80.0% (inside=94)
|30.0|Track C|12w|unstable|191|81|110|rise 22.2% (first) / 25.5% (second), flat 44.4% (first) / 52.7% (second), fall 33.3% (first) / 21.8% (second), diff={'rise': 0.03232323232323231, 'flat': 0.0828282828282828, 'fall': 0.11515151515151514}
|30.0|Track A|12w|stable|72|72|72|coverage 79.2% vs nominal 80.0% (inside=57)
|60.0|Track C|12w|unstable|96|36|60|rise 19.4% (first) / 28.3% (second), flat 33.3% (first) / 50.0% (second), fall 47.2% (first) / 21.7% (second), diff={'rise': 0.08888888888888888, 'flat': 0.16666666666666669, 'fall': 0.25555555555555554}
|60.0|Track A|12w|stable|37|37|37|coverage 89.2% vs nominal 80.0% (inside=33)