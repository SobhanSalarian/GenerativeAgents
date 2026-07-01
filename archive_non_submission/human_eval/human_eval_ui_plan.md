# Human Evaluation UI — Implementation Plan

## What we are building

A single-file Streamlit web app that runs locally on the rater's machine. The
rater opens one packet at a time, reads the agent's context and decision, fills
in four rating sliders and one yes/no question, and the app saves their scores
directly to the `human_eval_ratings.csv` file that `rating_ingestion.py`
already knows how to read. No server, no database, no accounts.

---

## Technology

| Choice | Why |
|---|---|
| **Streamlit** | Single Python file, runs with `streamlit run`, installs with `pip install streamlit`. No frontend knowledge needed. |
| **Single file** | `reverie/backend_server/human_eval_ui.py` — everything in one place, easy to share with raters |
| **Local only** | Rater runs it on their own machine, ratings go to a CSV file they send back |

---

## Step 1 — Project setup

**What this step does:** Create the file, define the one dependency, confirm
Streamlit is installed.

**File to create:** `reverie/backend_server/human_eval_ui.py`

**Dependency — tell raters to install:**

```bash
pip install streamlit
```

**How to run the app:**

```bash
cd reverie/backend_server
streamlit run human_eval_ui.py
```

This opens a browser tab at `http://localhost:8501` automatically.

**Validation:** App opens in the browser showing a blank page with no errors.

---

## Step 2 — Sidebar: file loader and rater ID

**What this step does:** Give the rater two inputs in the left sidebar —
(1) their rater ID, (2) the path to their packets file. When they click
"Load", the app reads the JSONL file into memory.

**What the sidebar looks like:**

```
┌─────────────────────────┐
│  Rater ID               │
│  [__________________]   │
│                         │
│  Packets file           │
│  [Browse...]            │
│                         │
│  [  Load packets  ]     │
│                         │
│  Progress: 12 / 96      │
│  ████████░░░░░  12%     │
└─────────────────────────┘
```

**What the code does:**

- `st.text_input("Rater ID")` — rater enters e.g. `rater_01`
- `st.file_uploader(...)` — rater selects their `human_eval_packets.jsonl`
- On load: reads every line of the JSONL into a Python list of dicts
- Checks if a `human_eval_ratings.csv` already exists alongside the JSONL. If
  it does, reads it and builds a set of `packet_id` values that are already
  rated — so the rater can resume where they left off without re-doing work

**Validation:** Load a real `human_eval_packets.jsonl`. Confirm the app shows
"X packets loaded" and the correct packet count.

---

## Step 3 — Session state (memory across interactions)

**What this step does:** Streamlit re-runs the whole script every time the
user clicks a button. Session state is the mechanism that keeps information
alive between those re-runs — specifically, which packet the rater is currently
on, and the ratings they have entered so far.

**Variables stored in `st.session_state`:**

| Variable | What it holds |
|---|---|
| `packets` | The full list of packets loaded from JSONL |
| `current_index` | Which packet the rater is looking at right now (0-based) |
| `already_rated` | Set of `packet_id` strings already saved to CSV |
| `rater_id` | The rater's identifier string |
| `ratings_path` | Path to the CSV file to write to |

**Logic:**

- When the app first loads, `current_index` starts at 0
- After loading the file, `current_index` is advanced past any packets already
  in `already_rated`
- When the rater clicks Save & Next (Step 6), `current_index` increments by 1

**Validation:** Load packets, rate one, reload the page — confirm the rater
lands on packet 2, not packet 1.

---

## Step 4 — Packet display area

**What this step does:** Show the rater everything they need to make an
informed rating for the current packet. The layout is top-to-bottom, reading
order.

**Layout:**

```
┌──────────────────────────────────────────────────────────┐
│  Packet 13 of 96  •  Phase: middle  •  Trial 2  Step 47 │
├──────────────────────────────────────────────────────────┤
│  AGENT BACKGROUND                                        │
│  Agent ID: agent_3f8a1c2d                               │
│  [persona background text...]                            │
├──────────────────────────────────────────────────────────┤
│  SITUATION                                               │
│  Community fund: 412 credits (41% of capacity)          │
│  Fair share this round: 6.25 credits                    │
│  Group total requested last round: 68 credits           │
│  Group stayed within sustainable limit: No              │
├──────────────────────────────────────────────────────────┤
│  AGENT'S MEMORY (what was injected into this decision)  │
│  • Round 44: group demanded 72 credits vs 50 available  │
│  • Round 45: pool dropped from 480 to 458               │
│  • [etc.]                                                │
├──────────────────────────────────────────────────────────┤
│  AGENT'S PLAN REFERENCE                                  │
│  "I want to support my research while being mindful..."  │
├──────────────────────────────────────────────────────────┤
│  DECISION                                                │
│  Requested: 8 credits  │  Granted: 8 credits            │
│                                                          │
│  Reasoning:                                              │
│  "Given that the group has been over-requesting, I       │
│   will limit myself to just above fair share this        │
│   round to help stabilise the fund..."                   │
│                                                          │
│  Memory cited: "Last round the group took 72..."         │
└──────────────────────────────────────────────────────────┘
```

**Rules:**

- Condition label is **not shown** (blinded)
- Agent name is **not shown** — only `blinded_agent_id`
- Empty fields (no memory, no plan) display as `— not available —`, not blank

**Validation:** Step through 5 packets and confirm all fields display
correctly, none show raw Python `None`, persona names are not visible.

---

## Step 5 — Rating widgets

**What this step does:** Show the four 1–5 sliders with rubric anchor text
visible alongside each one, the yes/no believability question, and a notes box.

**Layout of the rating section:**

```
┌──────────────────────────────────────────────────────────┐
│  RATINGS                                                 │
│                                                          │
│  1. Behavioural Consistency                              │
│     Does the agent act consistently with its persona     │
│     and prior behaviour?                                 │
│     1 = Contradicts persona    5 = Fully consistent      │
│     [  1  ──●──────────────  5  ]   Current: 2          │
│                                                          │
│  2. Memory Coherence                                     │
│     Does the agent appropriately use its prior           │
│     interaction history in this decision?                │
│     1 = Ignores / misuses memory   5 = Uses it well      │
│     [  1  ────────●────────  5  ]   Current: 3          │
│                                                          │
│  3. Planning Plausibility                                │
│     Does the agent's stated plan connect logically       │
│     to its decision?                                     │
│     1 = No connection    5 = Clear logical connection    │
│     [  1  ──────────●──  5  ]   Current: 4              │
│                                                          │
│  4. Response Naturalness                                 │
│     Does the reasoning read as a believable human        │
│     response in this context?                            │
│     1 = Clearly robotic / templated    5 = Natural       │
│     [  1  ────────────●  5  ]   Current: 5              │
│                                                          │
│  Overall believability                                   │
│  Would a naive reader believe this agent is human?       │
│  ( ) Yes    ( ) No                                       │
│                                                          │
│  Notes (optional)                                        │
│  [_________________________________________________]     │
│                                                          │
│  [ ← Previous ]                  [ Save & Next → ]      │
└──────────────────────────────────────────────────────────┘
```

**Technical details:**

- `st.slider("Behavioural Consistency", min_value=1, max_value=5, value=3)` —
  default 3 (neutral), not 1, so the rater must actively move the slider
- `st.radio("Overall believability", ["Yes", "No"])` — no pre-selected default
  so the rater must actively choose
- `st.text_area("Notes")` — optional, can be left blank
- All five inputs **reset to their defaults** when moving to the next packet —
  so the rater cannot accidentally carry over previous ratings

**Validation:** Rate 3 packets in a row. Open the CSV and confirm each row has
a different `packet_id` and the correct values in all columns.

---

## Step 6 — Save logic

**What this step does:** When the rater clicks "Save & Next", write one new
row to the CSV and move to the next unrated packet.

**The row written matches exactly what `rating_ingestion.py` expects:**

```
packet_id, blinded_agent_id, scenario, trial, step, phase,
rater_id, behavioural_consistency, memory_coherence,
planning_plausibility, response_naturalness, believable_yes_no, notes
```

**How saving works:**

- The CSV is opened in **append mode** (`'a'`) — never overwritten
- If the CSV does not exist yet, it is created with the header row first
- After writing, the `packet_id` is added to `st.session_state.already_rated`
- `current_index` advances to the next unrated packet
- The sliders reset to their defaults
- If the rater is on the last packet, show a "All done — thank you" message
  instead of moving forward

**Important:** The app never holds all ratings in memory waiting for a final
submit. Every "Save & Next" writes immediately. If the rater's browser crashes,
no work is lost beyond the current unsaved packet.

**Validation:** Rate 5 packets, close the browser, reopen the app, reload the
same file — confirm it resumes at packet 6 and the CSV has exactly 5 rows.

---

## Step 7 — Navigation and progress

**What this step does:** Let the rater go back to a previous packet if they
want to change a rating, and always know how far through their work they are.

**Progress bar:**
`st.progress(rated_count / total_count)` shown in the sidebar with a label
such as "47 / 96 rated".

**Previous button:** Goes back one packet. The existing rating for that packet
is loaded from the CSV and pre-filled into the sliders so the rater sees what
they already entered — they are not rating blind. If they click "Save & Next"
again, the row is **updated** (old row replaced, not duplicated).

**Skip button (optional, lower priority):** Lets the rater skip a difficult
packet and come back to it. Skipped packets are shown at the end. Include only
if straightforward to add after the core steps are complete.

**Validation:** Rate packets 1–5, click Previous twice, change the rating for
packet 4, click Save & Next — confirm the CSV has the updated value for that
`packet_id`, not two rows for the same packet.

---

## Step 8 — Rater instructions page

**What this step does:** The first thing the rater sees when they open the app
is a brief instructions page, not the rating interface. This replaces the need
to send a separate instructions document.

**Content of the instructions page:**

- What the study is about (one short paragraph, no details that could bias
  ratings)
- What each of the four dimensions means, copied from the rubric:

| Dimension | What to assess |
|---|---|
| Behavioural consistency | Does the agent act in line with its persona and prior behaviour? |
| Memory coherence | Does the agent appropriately retrieve and use prior interaction history? |
| Planning plausibility | Does the agent's stated plan connect logically to its decision? |
| Response naturalness | Does the reasoning read as a believable human response in context? |

- The 1–5 anchor definitions for each dimension
- How to handle missing information — if the memory section shows "— not
  available —", score memory coherence as 1 (no evidence of memory use)
- How long it will take — approximately 7 hours total; can be done in
  multiple sessions, progress is saved automatically
- How to submit — send the `human_eval_ratings.csv` file back when complete

**Navigation:** A single "I understand — begin rating" button takes the rater
to the packet interface.

**Validation:** Read the instructions page and confirm all rubric anchors match
the methodology chapter (§X.4.1–§X.4.4).

---

## File structure when complete

```
reverie/backend_server/
├── human_eval_ui.py          ← new file (~300 lines, single file)
├── human_evaluation.py       ← unchanged (generates packets)
├── rating_ingestion.py       ← unchanged (ingests completed CSVs)
```

**Rater workflow end to end:**

```
1. pip install streamlit
2. streamlit run human_eval_ui.py
3. Enter rater ID, load human_eval_packets.jsonl
4. Rate packets one by one — progress saves automatically
5. Send human_eval_ratings.csv back to researcher
6. Researcher runs: python rating_ingestion.py experiment_results_ic_primary/
```

---

## Build order summary

| Step | What it delivers | Validates independently? |
|---|---|---|
| 1 | App opens in browser | Yes — no errors on load |
| 2 | File loads, packet count shown | Yes — check packet count |
| 3 | Resume works after reload | Yes — reload and check index |
| 4 | Packet displays correctly | Yes — check all fields render |
| 5 | Sliders and buttons render | Yes — check CSV values |
| 6 | CSV row written correctly | Yes — open CSV after each save |
| 7 | Progress and back-navigation work | Yes — check CSV after editing |
| 8 | Instructions page complete | Yes — read against rubric |

Each step builds on the previous one and is validated before the next begins.

---

## Notes for implementation

- Estimated build time: one session
- Estimated lines of code: ~300
- No external dependencies beyond `streamlit` (already Python standard CSV,
  JSON modules used elsewhere in the pipeline)
- The CSV schema is fixed — do not change column names or order, as
  `rating_ingestion.py` reads them by name
- The `packet_id` and `blinded_agent_id` fields come directly from the packet
  and must be written to the CSV unchanged — they are the join keys used by
  the analysis pipeline
