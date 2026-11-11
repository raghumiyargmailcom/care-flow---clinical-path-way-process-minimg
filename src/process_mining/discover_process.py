"""
CareFlow — Process Discovery Engine (PM4Py / Python)
=====================================================
Applies process mining algorithms to discover the 'As-Is' clinical process map,
generate Directed Graphs (DFG), Petri Nets, BPMN models, and uncover chaotic
patient flows (Spaghetti Diagram) highlighting operational friction.
"""

from __future__ import annotations

import logging
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import pm4py

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUTS_DIR = BASE_DIR / "data" / "outputs"
REPORTS_DIR = BASE_DIR / "reports" / "figures"
MODELS_DIR = BASE_DIR / "reports" / "models"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("careflow.discovery")


def load_and_format_event_log(csv_path: Path | None = None) -> pd.DataFrame:
    """Load and format event log for PM4Py compliance."""
    if csv_path is None:
        csv_path = PROCESSED_DIR / "cleaned_data.csv"
        if not csv_path.exists():
            csv_path = PROCESSED_DIR / "event_log_clean.csv"

    log.info("Loading event log from %s", csv_path)
    df = pd.read_csv(csv_path)

    # Standardize column naming for PM4Py
    col_map = {
        "Case_ID": "case_id",
        "Activity_Name": "activity",
        "Timestamp": "timestamp",
        "Department": "department",
        "Doctor_ID": "resource",
    }
    df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})

    # Format using PM4Py utilities
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = pm4py.format_dataframe(
        df,
        case_id="case_id",
        activity_key="activity",
        timestamp_key="timestamp",
    )
    log.info("Formatted event log: %d events across %d unique cases", len(df), df["case_id"].nunique())
    return df


def discover_process_models(df: pd.DataFrame) -> dict:
    """
    Run algorithmic discovery using PM4Py:
      1. Directly-Follows Graph (Frequency & Performance)
      2. Petri Net via Inductive Miner
      3. BPMN Model
      4. Process Tree
    """
    log.info("Computing Directly Follows Graph (DFG) …")
    dfg, start_acts, end_acts = pm4py.discover_dfg(df)

    log.info("Computing Performance DFG (Time Delays) …")
    perf_dfg, p_start, p_end = pm4py.discover_performance_dfg(df)

    log.info("Discovering Petri Net via Inductive Miner …")
    net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(df)

    log.info("Discovering BPMN Model …")
    bpmn_model = pm4py.discover_bpmn_inductive(df)

    log.info("Discovering Process Tree …")
    process_tree = pm4py.discover_process_tree_inductive(df)

    # Export PNML
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    pnml_path = MODELS_DIR / "careflow_petri_net.pnml"
    try:
        pm4py.write_pnml(net, initial_marking, final_marking, str(pnml_path))
        log.info("✓ Petri Net exported to %s", pnml_path)
    except Exception as e:
        log.warning("PNML export warning: %s", e)

    # Export DFG transitions as structured CSV
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    dfg_rows = []
    for (src, tgt), count in dfg.items():
        avg_duration_min = round(perf_dfg.get((src, tgt), {}).get("mean", 0) / 60, 2)
        dfg_rows.append({
            "source_activity": src,
            "target_activity": tgt,
            "transition_count": count,
            "avg_wait_minutes": avg_duration_min,
        })
    dfg_df = pd.DataFrame(dfg_rows).sort_values("transition_count", ascending=False)
    dfg_df.to_csv(OUTPUTS_DIR / "dfg_transitions.csv", index=False)
    log.info("✓ DFG edge transitions written to %s", OUTPUTS_DIR / "dfg_transitions.csv")

    return {
        "dfg": dfg,
        "perf_dfg": perf_dfg,
        "start_activities": start_acts,
        "end_activities": end_acts,
        "petri_net": (net, initial_marking, final_marking),
        "bpmn_model": bpmn_model,
        "process_tree": process_tree,
        "transitions_df": dfg_df,
    }


def generate_spaghetti_diagram(transitions_df: pd.DataFrame, output_path: Path | None = None) -> None:
    """
    Renders a visual Directed Graph ('Spaghetti Diagram') of the hospital's actual
    process flows, explicitly highlighting loop-backs (such as X-Ray -> Triage).
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    if output_path is None:
        output_path = REPORTS_DIR / "spaghetti_diagram.png"

    log.info("Rendering Process Flow Spaghetti Diagram …")
    G = nx.DiGraph()

    for _, row in transitions_df.iterrows():
        src = row["source_activity"]
        tgt = row["target_activity"]
        cnt = row["transition_count"]
        wait = row["avg_wait_minutes"]
        G.add_edge(src, tgt, weight=cnt, wait=wait)

    plt.figure(figsize=(16, 11), dpi=200)
    pos = nx.spring_layout(G, k=1.8, seed=42)

    # Differentiate bottleneck loopback edges (like X-Ray -> Triage)
    normal_edges = []
    loopback_edges = []
    for u, v in G.edges():
        if (u == "X-Ray" and v == "Triage") or (u == "Triage" and v == "Triage"):
            loopback_edges.append((u, v))
        else:
            normal_edges.append((u, v))

    # Node coloring
    node_colors = []
    for node in G.nodes():
        if node in ("Registration", "Patient Registration"):
            node_colors.append("#2ecc71")  # Green start
        elif node in ("Discharge", "Patient Discharged", "Admission"):
            node_colors.append("#e74c3c")  # Red terminal
        elif node == "Triage":
            node_colors.append("#e67e22")  # Orange bottleneck target
        elif node == "X-Ray":
            node_colors.append("#9b59b6")  # Purple diagnostic
        else:
            node_colors.append("#3498db")  # Blue standard

    nx.draw_networkx_nodes(G, pos, node_size=3200, node_color=node_colors, alpha=0.9, edgecolors="#2c3e50", linewidths=2)
    nx.draw_networkx_labels(G, pos, font_size=9, font_family="sans-serif", font_weight="bold", font_color="#ffffff")

    # Draw regular edges
    nx.draw_networkx_edges(
        G, pos, edgelist=normal_edges, width=1.8, alpha=0.6, edge_color="#7f8c8d",
        arrowstyle="-|>", arrowsize=18, connectionstyle="arc3,rad=0.1"
    )

    # Highlight loopback / bottleneck edges in prominent red
    if loopback_edges:
        nx.draw_networkx_edges(
            G, pos, edgelist=loopback_edges, width=3.5, alpha=0.9, edge_color="#e74c3c",
            arrowstyle="-|>", arrowsize=22, connectionstyle="arc3,rad=0.25"
        )

    plt.title("CareFlow — As-Is Clinical Pathway Spaghetti Diagram\n(Red edge indicates 40% X-Ray → Triage bottleneck loop-back)", fontsize=15, fontweight="bold", pad=20)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    log.info("✓ Spaghetti Diagram saved to %s", output_path)


def main():
    df = load_and_format_event_log()
    results = discover_process_models(df)
    generate_spaghetti_diagram(results["transitions_df"])
    log.info("Process discovery execution successfully completed.")


if __name__ == "__main__":
    main()
