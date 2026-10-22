# Model settings per stat

Each candidate fitted 2013-2022, stopped early on 2023, scored on 2024 (log-likelihood per player-game, against the defaults). The best on 2024 is then checked on 2025-2026, never seen; adopted unless worse there by more than one standard error.

## Disposals

| setting | 2024 change vs defaults |
|---|---|
| defaults | +0.00000 ± 0.00000 |
| {"num_leaves": 15} | +0.00071 ± 0.00035 |
| {"num_leaves": 63} | +0.00022 ± 0.00037 |
| {"min_child_samples": 50} | +0.00058 ± 0.00027 |
| {"min_child_samples": 500} | +0.00028 ± 0.00031 |
| {"colsample_bytree": 0.5} | +0.00059 ± 0.00033 |
| {"num_leaves": 15, "min_child_samples": 500} | +0.00080 ± 0.00039 |
| {"num_leaves": 63, "min_child_samples": 100, "colsample_bytree": 0.5} | +0.00007 ± 0.00042 |
| {"reg_lambda": 10.0} | -0.00016 ± 0.00014 |
| {"learning_rate": 0.01, "n_estimators": 6000} | +0.00024 ± 0.00025 |

best on 2024: {"num_leaves": 15, "min_child_samples": 500}; on 2025-2026 it changes log-likelihood by +0.00026 ± 0.00030: adopted

## Marks

| setting | 2024 change vs defaults |
|---|---|
| defaults | +0.00000 ± 0.00000 |
| {"num_leaves": 15} | -0.00022 ± 0.00035 |
| {"num_leaves": 63} | -0.00043 ± 0.00037 |
| {"min_child_samples": 50} | -0.00085 ± 0.00033 |
| {"min_child_samples": 500} | -0.00031 ± 0.00038 |
| {"colsample_bytree": 0.5} | -0.00028 ± 0.00034 |
| {"num_leaves": 15, "min_child_samples": 500} | -0.00017 ± 0.00041 |
| {"num_leaves": 63, "min_child_samples": 100, "colsample_bytree": 0.5} | -0.00065 ± 0.00044 |
| {"reg_lambda": 10.0} | -0.00028 ± 0.00020 |
| {"learning_rate": 0.01, "n_estimators": 6000} | -0.00073 ± 0.00033 |

defaults kept (no candidate beat them on 2024)

## Tackles

| setting | 2024 change vs defaults |
|---|---|
| defaults | +0.00000 ± 0.00000 |
| {"num_leaves": 15} | +0.00064 ± 0.00030 |
| {"num_leaves": 63} | +0.00008 ± 0.00029 |
| {"min_child_samples": 50} | -0.00019 ± 0.00019 |
| {"min_child_samples": 500} | -0.00025 ± 0.00023 |
| {"colsample_bytree": 0.5} | -0.00002 ± 0.00027 |
| {"num_leaves": 15, "min_child_samples": 500} | +0.00039 ± 0.00030 |
| {"num_leaves": 63, "min_child_samples": 100, "colsample_bytree": 0.5} | -0.00018 ± 0.00043 |
| {"reg_lambda": 10.0} | +0.00018 ± 0.00030 |
| {"learning_rate": 0.01, "n_estimators": 6000} | +0.00033 ± 0.00024 |

best on 2024: {"num_leaves": 15}; on 2025-2026 it changes log-likelihood by -0.00052 ± 0.00021: vetoed, defaults kept

## Goals

| setting | 2024 change vs defaults |
|---|---|
| defaults | +0.00000 ± 0.00000 |
| {"num_leaves": 15} | +0.00047 ± 0.00031 |
| {"num_leaves": 63} | -0.00010 ± 0.00035 |
| {"min_child_samples": 50} | -0.00011 ± 0.00030 |
| {"min_child_samples": 500} | -0.00002 ± 0.00035 |
| {"colsample_bytree": 0.5} | +0.00017 ± 0.00033 |
| {"num_leaves": 15, "min_child_samples": 500} | +0.00066 ± 0.00034 |
| {"num_leaves": 63, "min_child_samples": 100, "colsample_bytree": 0.5} | -0.00007 ± 0.00041 |
| {"reg_lambda": 10.0} | +0.00006 ± 0.00020 |
| {"learning_rate": 0.01, "n_estimators": 6000} | +0.00056 ± 0.00025 |

best on 2024: {"num_leaves": 15, "min_child_samples": 500}; on 2025-2026 it changes log-likelihood by +0.00014 ± 0.00023: adopted

The gains here are small next to the inputs: settings matter less than what the model is given.

