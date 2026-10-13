# CareFlow — Methodology

## 1. Project Approach

CareFlow applies **process mining** to synthetic clinical pathway data. Process mining is a family of techniques that extracts knowledge from event logs recorded by information systems, enabling objective analysis of actual process behaviour versus documented (ideal) process models.

The three core process-mining tasks implemented are:

| Task | Question Answered | Method |
|---|---|---|
| **Process Discovery** | What process do patients actually follow? | Inductive Miner, Alpha Miner |
| **Conformance Checking** | How closely does actual behaviour match the ideal process? | Token Replay, Alignment-based |
| **Performance Analysis** | Where are the bottlenecks and delays? | Waiting-time analysis, DFG annotation |

---

## 2. Data Generation Methodology

### 2.1 Synthetic Patient Pathways

Patients are assigned a **priority level** drawn from a weighted distribution (P1: 10%, P2: 25%, P3: 40%, P4: 25%). Each priority maps to a different clinical pathway profile that determines:
- Which diagnostic activities are performed
- Whether observation, reassessment, or specialist referral occurs
- The likely final disposition (discharged, admitted, transferred, LWBS)

### 2.2 Duration Sampling

Activity durations are sampled from a **log-normal distribution** applied to each activity's reference (expected) duration. This produces the right-skewed distribution typical of clinical activity times, where most events are close to the expected duration but occasional events take much longer.

### 2.3 Deliberate Bottlenecks

The following activities have **inflated wait multipliers** to simulate real-world hospital bottlenecks, suitable for testing detection algorithms:

| Activity | Multiplier | Simulated Cause |
|---|---|---|
| CT Scan | 3.0× | Single scanner, high demand |
| Blood Test | 2.0× | Lab processing backlog |
| Admission | 2.5× | Bed unavailability |
| Observation | 2.0× | Extended monitoring periods |

### 2.4 Realistic Variations

- **Inter-activity waiting:** Exponentially distributed waiting times (mean 15 min) between activities simulate queue dynamics.
- **Non-completed events:** ~12% of events are skipped, cancelled, or pending to reflect real-world process deviations.
- **Delay reasons:** Applicable to ~12–40% of events (higher for bottleneck activities), drawn from realistic categories.
- **Repeated activities:** Reassessment loops and repeated blood tests are included as deliberate process loops.

### 2.5 Reproducibility

A fixed random seed (`RANDOM_SEED = 42`) is set for both NumPy and Python's `random` module before any stochastic operation. This ensures identical output across runs.

---

## 3. Process Mining Algorithms

### 3.1 Process Discovery

**Directly-Follows Graph (DFG)**  
The DFG captures how often each activity directly follows another, providing a simple frequency-annotated process map.

**Inductive Miner (IM)**  
The Inductive Miner (Leemans et al., 2013) recursively cuts the DFG into sub-logs using split operators (sequence, parallel, exclusive choice, loop). This guarantees a sound Petri net output with measurable fitness.

### 3.2 Conformance Checking

**Token Replay**  
Replays each case trace against the discovered Petri net, tracking token production and consumption. Outputs:
- **Fitness** — proportion of traces that can be replayed without violations
- **Precision** — how much behaviour the model allows beyond what was observed

**Alignment-based Conformance**  
Finds the optimal alignment between each trace and the model, quantifying the cost of deviations. More accurate than token replay for complex models.

### 3.3 Performance Analysis

Waiting times and dwell times are annotated onto the DFG to produce a **performance DFG**, showing which transitions are the slowest. KPIs include:
- Average and median LoS by priority
- Triage-to-doctor time (4-hour target proxy)
- Bottleneck activity identification via percentile dwell-time analysis

---

## 4. Validation Framework

Data validation is performed at two stages:

1. **Pre-write validation** (in `generate_dataset.py`) — checks nulls, enum membership, ID consistency, and timestamp monotonicity before files are written.
2. **Post-load cleaning** (in `validate_and_clean.py`) — enforces schema, removes duplicates, repairs timestamps, and derives additional features.

---

## 5. Ethical Considerations

- All data is **entirely synthetic**. No real patient, clinician, or hospital data is used.
- Age is represented as a **broad group** (not date of birth) to prevent re-identification risk even in a synthetic context.
- Doctor IDs are pseudonymous codes (`DR001–DR040`) with no real-world mapping.
- Findings from this project **must not** be used to make clinical decisions or claims about real hospital performance.
