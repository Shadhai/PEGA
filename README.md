<div align="center">

# 🛡️ CINT-70 / PAGA

### **P**lan-**A**gnostic **G**raph-Grounded **A**ction Assurance for Embodied Agents

*A pre-execution assurance layer that validates robotic action plans against graph-grounded physical constraints, before anything moves.*

![Unsafe Acceptance Rate](https://img.shields.io/badge/UAR-0.000-brightgreen)
![F1](https://img.shields.io/badge/F1-1.000-brightgreen)
![Z3](https://img.shields.io/badge/Z3%20checks-219%20%7C%200%20disagreements-blue)
![Hardware](https://img.shields.io/badge/runs%20on-4%20GB%20VRAM-orange)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

</div>

---

## 📑 Table of Contents

- [Highlights](#-highlights)
- [Domains](#-domains)
- [Quick Start](#-quick-start)
- [Benchmarks & Usage](#-benchmarks--usage)
- [Dataset Composition](#-dataset-composition)
- [Metrics](#-metrics)
- [Results](#-results)
- [Domain-Specific Settings](#-domain-specific-settings)
- [Repository Guide](#-repository-guide)
- [Outputs](#-outputs)
- [Known Limitations](#-known-limitations)
- [Reproducibility](#-reproducibility)
- [Data & License](#-data--license)

---

## ✨ Highlights

| Metric | Value |
|--------|-------|
| 🚀 Aerospace benchmark | **273 tasks** (195 safe, 78 unsafe) |
| 🏭 Industrial benchmark | **150 tasks** (75 safe, 75 unsafe) |
| 🎯 Precision / Recall / F1 | **1.000** (both domains) |
| ⛔ Unsafe Acceptance Rate (UAR) | **0.000** |
| 🎲 Multi-seed variance | **± 0.000** |
| 📈 AUC-ROC / AUC-PR | **1.000 / 1.000** |
| 🧮 Z3 formal verification | **219 checks, 0 disagreements** |
| 💻 Consumer hardware | **4 GB VRAM, zero cloud cost** |

---

## 🌍 Domains

| Domain | Scope |
|--------|-------|
| 🛰️ **Aerospace** | ISS Canadarm2, Mars 2020 |
| 🏭 **Industrial** | UR-5-class workcell |

---

## ⚡ Quick Start

**Kaggle workflow**

1. Add the dataset as an **Input** (e.g. `joseph7891/newer-updateed-70` or `cint70-ablation-package`).
2. Run the **bootstrap cell** after *every* kernel restart. It copies the input to `/kaggle/working/cint70` and applies patches.
3. Run a benchmark (see below).

```bash
cd /kaggle/working/cint70
python tests/test_smoke.py          # sanity check first
```

---

## 🧪 Benchmarks & Usage

```bash
cd /kaggle/working/cint70

# Industrial: full run (150 tasks)
python run_benchmark.py --domain industrial

# Industrial: per-hazard breakdown
python run_benchmark.py --domain industrial --per-hazard

# Industrial: ablations
python run_benchmark.py --domain industrial --ablation

# Space: validation-only on stored plans
python run_benchmark.py --domain space --per-hazard

# Both domains
python run_benchmark.py --domain both

# Legacy industrial-only runner
python run_industrial_eval.py
python run_industrial_eval.py --ablation

# Smoke tests
python tests/test_smoke.py
```

---

## 📦 Dataset Composition

| Domain | Tasks | Safe | Unsafe | Plan fields |
|--------|------:|-----:|-------:|-------------|
| Industrial | 150 | 75 | 75 | safe → `ground_truth_plan`, unsafe → `adversarial_plan` |
| Space | 273 | 195 | 78 | `ground_truth_plan` / `adversarial_plan` |

> ℹ️ Always report counts from the exact `task_library.json` you ran.

**Industrial constraint files**

| File | Notes |
|------|-------|
| `data/extracted/joint_limits_industrial.json` | Joint limits |
| `data/extracted/obstacle_map_industrial.json` | `worker_zone.clearance_m = 0.90` |
| `data/extracted/tool_catalog_industrial.json` | Tool catalog |

---

## 📐 Metrics

| Metric | Definition |
|--------|------------|
| **TP** | Unsafe plan correctly **rejected** |
| **FN** | Unsafe plan incorrectly **accepted** |
| **TN** | Safe plan correctly **approved** |
| **FP** | Safe plan incorrectly **rejected** |
| **Precision** | `TP / (TP + FP)` |
| **Recall** | `TP / (TP + FN)` |
| **F1** | Harmonic mean of precision and recall |
| **UAR** ⭐ | `FN / (TP + FN)`: **Unsafe Acceptance Rate**, the primary safety metric |

---

## 🏆 Results

### Industrial: full system (locked)

```
TP=75   FN=0   FP=0   TN=75
Precision=1.000   Recall=1.000   F1=1.000   UAR=0.000
```

### Industrial: ablation (150 tasks)

| Configuration | UAR ↓ | F1 ↑ |
|---------------|:-----:|:----:|
| ✅ `full` | 0.000 | 1.000 |
| `no_trajectory` | 0.000 | 1.000 |
| `no_kinematics` | 0.187 | 0.897 |
| `no_force_check` | 0.213 | 0.881 |
| `graph_only` | 0.400 | 0.750 |
| `no_graph` | 0.600 | 0.571 |
| `kinematics_only` | 0.813 | 0.315 |

Removing the graph-grounded constraints or the kinematic/force checks sharply degrades safety, so no single component is sufficient on its own.

---

## ⚙️ Domain-Specific Settings

| Setting | Value |
|---------|-------|
| Industrial max reach | **1.8 m** (`src/validator/reach.py`) |
| Space max reach | **17.6 m** |
| Kuzu DB path | File-style `data/graph_db_{domain}.kuzu` (only the parent dir is created) |
| LLM planner | **Not loaded** on the validation path; plans come from the task library |

---

## 🗂️ Repository Guide

| Script | Role |
|--------|------|
| `run_benchmark.py` | Unified runner: `--domain` / `--ablation` / `--per-hazard` |
| `run_industrial_eval.py` | Industrial-only runner |
| `tests/test_smoke.py` | Regression: files, reach, clearance, full 150 perfect |
| `src/validator/reach.py` | Domain-aware Euclidean reach check |
| `src/graph/queries.py` | Graph constraints (domain-aware industrial files) |

---

## 📤 Outputs

Result JSONs are written to `logs/benchmarks/`:

- `benchmark_industrial_hazard.json`
- `benchmark_industrial_ablation.json`
- `benchmark_space_hazard.json`
- `benchmark_both.json`
- `industrial_full.json` / `industrial_ablation.json`

---

## ⚠️ Known Limitations

- **Trajectory ablation:** `no_trajectory` matches the full system on this task set (endpoint-dominated plans).
- **Space counts:** the library may differ slightly from older paper text; report counts from the JSON actually used.
- **Scope:** the runners evaluate the **assurance layer** on stored plans. The full LLM planning path is separate.
- **Baselines:** no external baselines (SayCan / DoReMi-style) are included yet.

---

## 🔁 Reproducibility

The working directory is **ephemeral** on Kaggle. After every kernel restart:

1. Run the bootstrap cell (input dataset + patches).
2. Run `python run_benchmark.py ...` or `python tests/test_smoke.py`.

---

## 📚 Data & License

- **Data sources:** see [`SOURCES.md`](SOURCES.md).
- **License:** [MIT](LICENSE).
