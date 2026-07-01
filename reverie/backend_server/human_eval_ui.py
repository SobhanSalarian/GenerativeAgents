"""
Local Streamlit UI for blinded human evaluation packets.

Run from this directory with:
    streamlit run human_eval_ui.py
"""
from __future__ import annotations

import csv
import html
import io
import json
from pathlib import Path
from typing import Any

import streamlit as st


FIELDNAMES = [
    "packet_id",
    "blinded_agent_id",
    "scenario",
    "trial",
    "step",
    "phase",
    "rater_id",
    "behavioural_consistency",
    "memory_coherence",
    "planning_plausibility",
    "response_naturalness",
    "believable_yes_no",
    "notes",
]

RUBRICS = {
    "behavioural_consistency": {
        "label": "Behavioural Consistency",
        "question": "Does the agent act consistently with its persona and prior behaviour?",
        "low_anchor": "1 = Contradicts persona",
        "high_anchor": "5 = Fully consistent",
    },
    "memory_coherence": {
        "label": "Memory Coherence",
        "question": "Does the agent appropriately use its prior interaction history in this decision?",
        "low_anchor": "1 = Ignores / misuses memory",
        "high_anchor": "5 = Uses it well",
    },
    "planning_plausibility": {
        "label": "Planning Plausibility",
        "question": "Does the agent's stated plan connect logically to its decision?",
        "low_anchor": "1 = No connection",
        "high_anchor": "5 = Clear logical connection",
    },
    "response_naturalness": {
        "label": "Response Naturalness",
        "question": "Does the reasoning read as a believable human response in this context?",
        "low_anchor": "1 = Clearly robotic / templated",
        "high_anchor": "5 = Natural",
    },
}

RATER_CODES = ["R1", "R2", "R3", "R4", "R5"]

# Password gate — change this before sharing the tunnel URL with raters.
# Set to None to disable the password check.
APP_PASSWORD = "mres2026"


def init_state() -> None:
    defaults = {
        "packets": [],
        "current_index": 0,
        "already_rated": set(),
        "rater_id": "",
        "ratings_path": "",
        "ratings_by_packet": {},
        "instructions_seen": False,
        "loaded_source": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #202434;
            --muted: #697080;
            --line: #d8dde8;
            --panel: #ffffff;
            --soft: #f6f8fb;
            --accent: #315c96;
            --accent-soft: #eaf1fb;
        }
        .stApp {
            background: #f7f9fc;
            color: var(--ink);
        }
        .block-container {
            max-width: 1320px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label {
            font-size: 0.92rem;
        }
        h1, h2, h3 {
            color: var(--ink);
            letter-spacing: 0;
        }
        h1 {
            font-size: 2.5rem;
            line-height: 1.08;
            margin-bottom: 0.35rem;
        }
        h2 {
            font-size: 1.45rem;
            margin-top: 1.1rem;
        }
        h3 {
            font-size: 1.05rem;
        }
        .hero {
            background: linear-gradient(135deg, #ffffff 0%, #edf4ff 100%);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1.8rem 2rem;
            margin-bottom: 1.3rem;
        }
        .hero p {
            max-width: 880px;
            color: var(--muted);
            font-size: 1.05rem;
            line-height: 1.55;
            margin: 0.5rem 0 0;
        }
        .eyebrow {
            color: var(--accent);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }
        .section-title {
            color: var(--ink);
            font-size: 1rem;
            font-weight: 800;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            margin: 0.2rem 0 0.65rem;
        }
        .rubric-card, .info-card, .text-panel, .decision-panel {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem 1.05rem;
            min-height: 100%;
        }
        .rubric-card strong, .info-card strong {
            display: block;
            color: var(--ink);
            font-size: 1rem;
            margin-bottom: 0.45rem;
        }
        .rubric-card p, .info-card p {
            color: var(--muted);
            line-height: 1.5;
            margin: 0.25rem 0 0.75rem;
        }
        .anchor {
            display: block;
            background: var(--accent-soft);
            color: #23476f;
            border-radius: 6px;
            padding: 0.35rem 0.5rem;
            font-size: 0.86rem;
            font-weight: 650;
            line-height: 1.4;
            margin-top: 0.25rem;
        }
        .anchor-group {
            display: grid;
            gap: 0.3rem;
        }
        .meta-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin-top: 0.8rem;
        }
        .chip {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 999px;
            color: var(--ink);
            display: inline-flex;
            font-size: 0.88rem;
            font-weight: 650;
            padding: 0.35rem 0.7rem;
        }
        .muted {
            color: var(--muted);
        }
        .text-panel {
            color: #303647;
            font-size: 0.96rem;
            line-height: 1.58;
            white-space: normal;
        }
        .text-panel.empty {
            color: #8a91a0;
            font-style: italic;
        }
        .decision-panel {
            border-left: 4px solid var(--accent);
        }
        .decision-panel p {
            color: #303647;
            font-size: 1rem;
            line-height: 1.62;
            margin: 0.15rem 0 0;
        }
        .compact-metric {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 0.85rem 0.95rem;
        }
        .compact-metric .label {
            color: var(--muted);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .compact-metric .value {
            color: var(--ink);
            font-size: 1.18rem;
            font-weight: 800;
            margin-top: 0.25rem;
            overflow-wrap: anywhere;
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: #ffffff;
            border-color: var(--line);
            border-radius: 8px;
        }
        .stButton > button {
            border-radius: 6px;
            font-weight: 700;
        }
        .stSlider label, .stRadio label, .stTextArea label {
            font-weight: 700;
            color: var(--ink);
        }
        @media (max-width: 900px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }
            h1 {
                font-size: 2rem;
            }
            .hero {
                padding: 1.2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def display_value(value: Any) -> str:
    if value is None:
        return "-- not available --"
    if isinstance(value, str) and not value.strip():
        return "-- not available --"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def escape_text(value: Any) -> str:
    return html.escape(display_value(value)).replace("\n", "<br>")


def render_metric_card(label: str, value: Any) -> None:
    st.markdown(
        f"""
        <div class="compact-metric">
            <div class="label">{html.escape(label)}</div>
            <div class="value">{escape_text(value)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_text_panel(value: Any, empty: bool | None = None) -> None:
    text = display_value(value)
    is_empty = empty if empty is not None else text == "-- not available --"
    class_name = "text-panel empty" if is_empty else "text-panel"
    st.markdown(
        f'<div class="{class_name}">{escape_text(text)}</div>',
        unsafe_allow_html=True,
    )


def render_bullets(items: list[Any]) -> None:
    if not items:
        render_text_panel("-- not available --", empty=True)
        return
    bullet_html = "".join(f"<li>{escape_text(item)}</li>" for item in items)
    st.markdown(
        f'<div class="text-panel"><ul>{bullet_html}</ul></div>',
        unsafe_allow_html=True,
    )


def render_anchor_group(rubric: dict[str, str]) -> str:
    return (
        '<div class="anchor-group">'
        f'<span class="anchor">{html.escape(rubric["low_anchor"])}</span>'
        f'<span class="anchor">{html.escape(rubric["high_anchor"])}</span>'
        "</div>"
    )


def load_packets_from_path(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as infile:
        return parse_jsonl(infile)


def load_packets_from_upload(uploaded_file: Any) -> list[dict[str, Any]]:
    text = uploaded_file.getvalue().decode("utf-8")
    return parse_jsonl(io.StringIO(text))


def parse_jsonl(lines: Any) -> list[dict[str, Any]]:
    packets = []
    for line_number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            packets.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
    return packets


def read_rating_rows(ratings_path: Path) -> list[dict[str, str]]:
    if not ratings_path.exists():
        return []
    with ratings_path.open(newline="", encoding="utf-8") as infile:
        reader = csv.DictReader(infile)
        rows = []
        for row in reader:
            rows.append({field: row.get(field, "") for field in FIELDNAMES})
        return rows


def write_rating_rows(ratings_path: Path, rows: list[dict[str, str]]) -> None:
    ratings_path.parent.mkdir(parents=True, exist_ok=True)
    with ratings_path.open("w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def build_rating_index(
    rows: list[dict[str, str]], rater_id: str
) -> tuple[set[str], dict[str, dict[str, str]]]:
    rated = set()
    by_packet = {}
    for row in rows:
        if str(row.get("rater_id", "")).strip() != rater_id:
            continue
        packet_id = str(row.get("packet_id", "")).strip()
        if packet_id:
            rated.add(packet_id)
            by_packet[packet_id] = row
    return rated, by_packet


def first_unrated_index(packets: list[dict[str, Any]], rated: set[str]) -> int:
    for index, packet in enumerate(packets):
        if str(packet.get("packet_id", "")) not in rated:
            return index
    return len(packets)


def advance_to_next_unrated(start_index: int) -> None:
    packets = st.session_state.packets
    rated = st.session_state.already_rated
    for index in range(start_index, len(packets)):
        if str(packets[index].get("packet_id", "")) not in rated:
            st.session_state.current_index = index
            return
    st.session_state.current_index = len(packets)


def packet_count_text() -> str:
    total = len(st.session_state.packets)
    rated = len(st.session_state.already_rated)
    return f"{rated} / {total} rated"


def load_into_session(
    packets: list[dict[str, Any]],
    ratings_path: Path,
    rater_id: str,
    source_label: str,
) -> None:
    rows = read_rating_rows(ratings_path)
    rated, by_packet = build_rating_index(rows, rater_id)
    st.session_state.packets = packets
    st.session_state.rater_id = rater_id
    st.session_state.ratings_path = str(ratings_path)
    st.session_state.already_rated = rated
    st.session_state.ratings_by_packet = by_packet
    st.session_state.current_index = first_unrated_index(packets, rated)
    st.session_state.loaded_source = source_label


def existing_rating(packet_id: str) -> dict[str, str]:
    return st.session_state.ratings_by_packet.get(packet_id, {})


def parse_int_rating(row: dict[str, str], key: str, default: int = 3) -> int:
    try:
        value = int(float(row.get(key, default)))
    except (TypeError, ValueError):
        return default
    return min(5, max(1, value))


def upsert_rating(packet: dict[str, Any], values: dict[str, Any]) -> None:
    ratings_path = Path(st.session_state.ratings_path)
    rows = read_rating_rows(ratings_path)
    packet_id = str(packet.get("packet_id", ""))
    rater_id = str(st.session_state.rater_id).strip()

    new_row = {
        "packet_id": packet_id,
        "blinded_agent_id": str(packet.get("blinded_agent_id", "")),
        "scenario": str(packet.get("scenario", "")),
        "trial": str(packet.get("trial", "")),
        "step": str(packet.get("step", "")),
        "phase": str(packet.get("phase", "")),
        "rater_id": rater_id,
        "behavioural_consistency": str(values["behavioural_consistency"]),
        "memory_coherence": str(values["memory_coherence"]),
        "planning_plausibility": str(values["planning_plausibility"]),
        "response_naturalness": str(values["response_naturalness"]),
        "believable_yes_no": str(values["believable_yes_no"]),
        "notes": str(values.get("notes", "")),
    }

    replacement_index = None
    blank_template_index = None
    for index, row in enumerate(rows):
        if str(row.get("packet_id", "")).strip() != packet_id:
            continue
        row_rater_id = str(row.get("rater_id", "")).strip()
        if row_rater_id == rater_id:
            replacement_index = index
            break
        if not row_rater_id and blank_template_index is None:
            blank_template_index = index

    if replacement_index is not None:
        rows[replacement_index] = new_row
    elif blank_template_index is not None:
        rows[blank_template_index] = new_row
    else:
        rows.append(new_row)

    write_rating_rows(ratings_path, rows)
    st.session_state.already_rated.add(packet_id)
    st.session_state.ratings_by_packet[packet_id] = new_row


def render_instructions() -> None:
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">Blinded rating task</div>
            <h1>Human Evaluation</h1>
            <p>
                Review one agent decision packet at a time. Use the context,
                memory, plan, and reasoning shown on screen to judge whether the
                decision is coherent, plausible, and human-believable.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-title">The scenario</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="info-card" style="margin-bottom: 1rem;">
            <strong>Commons Dilemma</strong>
            <p>
                A group of eight AI agents share a common resource pool — a
                community fund of credits. Each round, every agent decides how
                many credits to request for their personal goal (research,
                creative work, etc.). The pool regenerates partially each round,
                but if total demand consistently exceeds what is sustainable the
                fund collapses and no one can draw from it.
            </p>
            <p>
                Agents vary in their architecture: some have access to memory of
                prior rounds, a long-term plan, and a reflection step; others
                do not. <strong>You do not know which architecture any agent
                has</strong> — that information is hidden. Your job is to rate
                how well each agent uses whatever information it visibly has
                available when making its decision.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-title">Variables you will see</div>', unsafe_allow_html=True)
    var_cols = st.columns(2)
    variables = [
        ("Resource before", "Credits remaining in the shared pool at the start of this round, before any requests are granted."),
        ("Pool percent", "The pool size as a percentage of its original starting capacity. 100% = full; values below ~50% indicate the pool is under stress."),
        ("Fair share", "The amount each agent would receive if the pool's safe regeneration capacity were divided equally among all agents. Requesting at or below this level is individually sustainable."),
        ("Group requested", "The total credits all agents requested this round combined. Values above the replenishment rate indicate collective over-extraction."),
        ("Resource level", "Credits remaining in the pool after all requests this round were granted. Lower than 'Resource before' when demand exceeded replenishment."),
        ("Coordinated", "Whether the group's collective demand this round stayed within the sustainable threshold. 'No' means the group over-extracted as a whole."),
        ("Memory cited", "A specific prior-round observation the agent retrieved and explicitly referenced in its reasoning. Blank if the agent cited none."),
        ("Plan reference", "A fragment of the agent's longer-term personal goal or strategy that it linked to this decision. Blank if the agent cited none."),
    ]
    for i, (term, defn) in enumerate(variables):
        with var_cols[i % 2]:
            st.markdown(
                f"""
                <div class="info-card" style="margin-bottom: 0.6rem;">
                    <strong>{html.escape(term)}</strong>
                    <p>{html.escape(defn)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("")
    st.markdown('<div class="section-title">Rating dimensions</div>', unsafe_allow_html=True)
    first_row = st.columns(2)
    second_row = st.columns(2)
    for column, rubric in zip(first_row + second_row, RUBRICS.values()):
        with column:
            st.markdown(
                f"""
                <div class="rubric-card">
                    <strong>{html.escape(rubric["label"])}</strong>
                    <p>{html.escape(rubric["question"])}</p>
                    {render_anchor_group(rubric)}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("")
    st.markdown('<div class="section-title">What is one packet?</div>', unsafe_allow_html=True)
    packet_cols = st.columns(2)
    with packet_cols[0]:
        st.markdown(
            """
            <div class="info-card">
                <strong>One packet = one decision to score</strong>
                <p>
                    A packet is everything needed to rate a single blinded agent
                    decision at one point in time. It contains the anonymous
                    agent ID, sanitised persona background, local situation,
                    available memories and plans, and the decision itself.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with packet_cols[1]:
        st.markdown(
            """
            <div class="info-card">
                <strong>Your task</strong>
                <p>
                    Read the evidence shown and judge how well the agent used
                    what it had available: persona, prior behaviour, recent
                    memories, current plan, and local context.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
    packet_detail_cols = st.columns(3)
    with packet_detail_cols[0]:
        st.markdown(
            """
            <div class="info-card">
                <strong>Agent</strong>
                <p>
                    Blinded ID plus sanitised background. Real names and
                    condition labels are hidden.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with packet_detail_cols[1]:
        st.markdown(
            """
            <div class="info-card">
                <strong>Situation</strong>
                <p>
                    Community resource state, fair share, group demand, and
                    sustainability/co-ordination context.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with packet_detail_cols[2]:
        st.markdown(
            """
            <div class="info-card">
                <strong>Decision</strong>
                <p>
                    Requested amount, granted amount, written reasoning, cited
                    memory, and cited plan reference.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    support_cols = st.columns(2)
    with support_cols[0]:
        st.markdown(
            """
            <div class="info-card">
                <strong>Missing information</strong>
                <p>
                    If a section shows "-- not available --", rate only from
                    the evidence shown. If memory is unavailable, score Memory
                    Coherence as 1.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with support_cols[1]:
        st.markdown(
            """
            <div class="info-card">
                <strong>Anonymous rater code</strong>
                <p>
                    Use the researcher-assigned code you were given, such as
                    R1, R2, or R3. Do not enter your name, email, or initials.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")
    support_cols = st.columns(2)
    with support_cols[0]:
        st.markdown(
            """
            <div class="info-card">
                <strong>Progress and submission</strong>
                <p>
                    The task can be completed across multiple sessions. Each
                    saved packet is written immediately to human_eval_ratings.csv.
                    Send that CSV back when complete.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with support_cols[1]:
        st.markdown(
            """
            <div class="info-card">
                <strong>Blinding reminder</strong>
                <p>
                    Packet condition and real agent identity are hidden. Rate
                    only from the evidence shown in each packet.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div class="info-card" style="margin-top: 1rem;">
            <strong>Estimated time</strong>
            <p>
                Approximately 7 hours total for the full packet set. You can stop
                and resume later using the same rater ID and packets file.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("")
    if st.button("I understand - begin rating", type="primary"):
        st.session_state.instructions_seen = True
        st.rerun()


def render_sidebar() -> None:
    with st.sidebar:
        st.header("Rating setup")
        current_rater = st.session_state.rater_id
        default_index = RATER_CODES.index(current_rater) if current_rater in RATER_CODES else 0
        rater_id = st.selectbox(
            "Assigned rater code",
            RATER_CODES,
            index=default_index,
            help=(
                "Use the anonymous code assigned by the researcher. "
                "Do not enter a name, email, or initials."
            ),
        )
        st.caption("Researcher-assigned anonymous code used for reliability analysis.")
        packets_path_text = st.text_input(
            "Packets file path",
            help="Best for local use: ratings save beside this JSONL file.",
        )
        uploaded_file = st.file_uploader(
            "Or browse for packets file",
            type=["jsonl"],
            help="If using browse only, ratings save in the current working directory.",
        )

        if st.button("Load packets", type="primary"):
            rater_id = rater_id.strip()
            if not rater_id:
                st.error("Enter a rater ID before loading packets.")
            else:
                try:
                    if packets_path_text.strip():
                        packets_path = Path(packets_path_text).expanduser()
                        packets = load_packets_from_path(packets_path)
                        ratings_path = packets_path.with_name("human_eval_ratings.csv")
                        source_label = str(packets_path)
                    elif uploaded_file is not None:
                        packets = load_packets_from_upload(uploaded_file)
                        ratings_path = Path.cwd() / "human_eval_ratings.csv"
                        source_label = uploaded_file.name
                    else:
                        raise ValueError("Choose a packets JSONL file first.")
                    load_into_session(packets, ratings_path, rater_id, source_label)
                    st.success(f"{len(packets)} packets loaded.")
                except Exception as exc:
                    st.error(f"Could not load packets: {exc}")

        total = len(st.session_state.packets)
        if total:
            rated = len(st.session_state.already_rated)
            st.divider()
            st.markdown("**Progress**")
            st.write(packet_count_text())
            st.progress(rated / total)
            st.caption(f"Ratings file: {st.session_state.ratings_path}")


def render_context_block(packet: dict[str, Any]) -> None:
    local_context = packet.get("local_context") or {}
    macro_state = local_context.get("macro_state") or {}
    decision = packet.get("decision") or {}

    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">Decision review</div>
            <h1>Packet {st.session_state.current_index + 1} of {len(st.session_state.packets)}</h1>
            <div class="meta-row">
                <span class="chip">Phase: {escape_text(packet.get("phase"))}</span>
                <span class="chip">Trial: {escape_text(packet.get("trial"))}</span>
                <span class="chip">Step: {escape_text(packet.get("step"))}</span>
                <span class="chip">Agent: {escape_text(packet.get("blinded_agent_id"))}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    is_ic = packet.get("scenario") == "information_consensus"

    st.markdown('<div class="section-title">Situation</div>', unsafe_allow_html=True)
    if is_ic:
        vote_tally = macro_state.get("vote_tally") or {}
        tally_display = ", ".join(
            f"Option {k}: {v}" for k, v in sorted(vote_tally.items())
        ) if vote_tally else "—"
        consensus_rate = macro_state.get("consensus_rate")
        consensus_pct = f"{round(consensus_rate * 100)}%" if consensus_rate is not None else "—"

        metric_cols = st.columns(3)
        with metric_cols[0]:
            render_metric_card("Consensus rate", consensus_pct)
        with metric_cols[1]:
            render_metric_card("Agents", macro_state.get("n_agents"))
        with metric_cols[2]:
            render_metric_card("Coordinated", macro_state.get("coordinated"))

        with st.container(border=True):
            st.markdown("**Vote tally this step**")
            st.write(tally_display)
            info_rate = macro_state.get("information_diffusion_rate")
            if info_rate is not None:
                st.write(f"Information diffusion rate: {info_rate:.2f}")
            consensus_reached = macro_state.get("consensus_reached")
            if consensus_reached:
                st.write(f"Consensus reached at step: {macro_state.get('consensus_step')}")
    else:
        metric_cols = st.columns(3)
        with metric_cols[0]:
            render_metric_card("Resource before", local_context.get("resource_level_before"))
        with metric_cols[1]:
            render_metric_card("Fair share", local_context.get("fair_share"))
        with metric_cols[2]:
            render_metric_card("Group requested", macro_state.get("total_requested"))

        metric_cols = st.columns(3)
        with metric_cols[0]:
            render_metric_card("Pool percent", local_context.get("pool_percent_before"))
        with metric_cols[1]:
            render_metric_card("Resource level", macro_state.get("resource_level"))
        with metric_cols[2]:
            render_metric_card("Coordinated", macro_state.get("coordinated"))

        with st.container(border=True):
            st.markdown("**Current situation notes**")
            st.write(f"Resource note: {display_value(macro_state.get('resource_level_note'))}")
            st.write(f"Current activity: {display_value(local_context.get('current_activity'))}")

    st.markdown('<div class="section-title">Agent background</div>', unsafe_allow_html=True)
    render_text_panel(packet.get("persona_background"))

    context_tabs = st.tabs(["Memory", "Daily goals", "Plan reference", "Decision"])
    with context_tabs[0]:
        render_bullets(local_context.get("recent_memories") or [])
    with context_tabs[1]:
        render_bullets(local_context.get("daily_goals") or [])
    with context_tabs[2]:
        render_text_panel(decision.get("plan_reference"))
    with context_tabs[3]:
        if is_ic:
            dec_cols = st.columns(3)
            with dec_cols[0]:
                render_metric_card("Option selected", decision.get("vote"))
            with dec_cols[1]:
                render_metric_card("Previous option", decision.get("prior_vote"))
            with dec_cols[2]:
                render_metric_card("Changed position", decision.get("position_change"))
            render_metric_card("Signal disclosed", decision.get("signal_disclosed"))
            st.markdown("**Statement shared with group**")
            render_text_panel(decision.get("shared_statement"))
        else:
            dec_cols = st.columns(2)
            with dec_cols[0]:
                render_metric_card("Requested", decision.get("requested"))
            with dec_cols[1]:
                render_metric_card("Granted", decision.get("granted"))
        st.markdown(
            f"""
            <div class="decision-panel" style="margin-top: 0.75rem;">
                <strong>Reasoning</strong>
                <p>{escape_text(decision.get("reasoning"))}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("")
        st.markdown("**Memory cited**")
        render_text_panel(decision.get("memory_reference"))


def render_ratings(packet: dict[str, Any]) -> None:
    packet_id = str(packet.get("packet_id", ""))
    saved = existing_rating(packet_id)
    st.markdown('<div class="section-title">Ratings</div>', unsafe_allow_html=True)

    values = {}
    for key, rubric in RUBRICS.items():
        with st.container(border=True):
            st.markdown(f"**{rubric['label']}**")
            st.caption(rubric["question"])
            st.markdown(
                render_anchor_group(rubric),
                unsafe_allow_html=True,
            )
            values[key] = st.slider(
                rubric["label"],
                min_value=1,
                max_value=5,
                value=parse_int_rating(saved, key),
                key=f"{packet_id}_{key}",
                label_visibility="collapsed",
            )

    saved_yes_no = str(saved.get("believable_yes_no", "")).strip()
    radio_options = ["Yes", "No"]
    radio_index = radio_options.index(saved_yes_no) if saved_yes_no in radio_options else None
    with st.container(border=True):
        values["believable_yes_no"] = st.radio(
            "Overall believability: Would a naive reader believe this agent is human?",
            radio_options,
            index=radio_index,
            horizontal=True,
            key=f"{packet_id}_believable_yes_no",
        )
        values["notes"] = st.text_area(
            "Notes (optional)",
            value=saved.get("notes", ""),
            key=f"{packet_id}_notes",
        )

    left, middle, right = st.columns([1, 2, 1])
    with left:
        if st.button("Previous", disabled=st.session_state.current_index <= 0):
            st.session_state.current_index -= 1
            st.rerun()
    with middle:
        if st.button("Skip for now"):
            next_index = min(st.session_state.current_index + 1, len(st.session_state.packets))
            advance_to_next_unrated(next_index)
            st.rerun()
    with right:
        if st.button("Save & Next", type="primary"):
            if not st.session_state.rater_id.strip():
                st.error("Missing rater ID. Reload the packets after entering a rater ID.")
            elif values["believable_yes_no"] is None:
                st.error("Choose Yes or No for overall believability before saving.")
            else:
                upsert_rating(packet, values)
                advance_to_next_unrated(st.session_state.current_index + 1)
                st.rerun()


def render_packet_interface() -> None:
    render_sidebar()
    packets = st.session_state.packets
    if not packets:
        st.markdown(
            """
            <div class="hero">
                <div class="eyebrow">Ready to start</div>
                <h1>Load packets</h1>
                <p>
                    Enter your rater ID in the sidebar, then load a
                    human_eval_packets.jsonl file. Ratings will save
                    automatically as you move through the packets.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if st.session_state.current_index >= len(packets):
        st.markdown(
            f"""
            <div class="hero">
                <div class="eyebrow">Complete</div>
                <h1>All done - thank you</h1>
                <p>Completed {html.escape(packet_count_text())}.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.info(f"Ratings saved to {st.session_state.ratings_path}")
        return

    packet = packets[st.session_state.current_index]
    context_col, rating_col = st.columns([1.45, 1], gap="large")
    with context_col:
        render_context_block(packet)
    with rating_col:
        render_ratings(packet)


def render_password_gate() -> bool:
    """Return True if the user has entered the correct password (or no password is set)."""
    if APP_PASSWORD is None:
        return True
    if st.session_state.get("authenticated"):
        return True
    st.markdown(
        "<h2 style='margin-top:4rem;text-align:center;'>Human Evaluation — Researcher Access</h2>",
        unsafe_allow_html=True,
    )
    col = st.columns([1, 2, 1])[1]
    with col:
        pw = st.text_input("Enter access password", type="password", key="_pw_input")
        if st.button("Enter", type="primary"):
            if pw == APP_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    return False


def main() -> None:
    st.set_page_config(page_title="Human Evaluation", layout="wide")
    inject_styles()
    if not render_password_gate():
        return
    init_state()
    if not st.session_state.instructions_seen:
        render_instructions()
    else:
        render_packet_interface()


if __name__ == "__main__":
    main()
