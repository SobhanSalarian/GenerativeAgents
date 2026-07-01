# AgentEval React Site

Standalone React/Vite website built from the `agent_eval_ui_kit.zip` assets and
component guidance. This version is a working browser-based human-evaluation
tool.

## Run locally

```bash
npm install
npm run dev
```

Then open the local URL printed by Vite.

## Evaluator workflow

1. Select the researcher-assigned rater code (`R1`-`R5`).
2. Upload `human_eval_packets.jsonl`.
3. Read each packet and complete the four 1-5 ratings, yes/no believability,
   and optional notes.
4. Click **Save & Next** after each packet.
5. Click **Download CSV** to export `human_eval_ratings.csv`.
6. Send the exported CSV back to the researcher.

Progress is saved in browser local storage for the selected rater code and
packet file name. Because this is a browser app, it cannot silently overwrite a
local CSV file on disk; the evaluator exports/downloads the completed CSV.

The exported CSV uses the same schema expected by `rating_ingestion.py`:

```text
packet_id, blinded_agent_id, scenario, trial, step, phase,
rater_id, behavioural_consistency, memory_coherence,
planning_plausibility, response_naturalness, believable_yes_no, notes
```

## Generative agent profile images

The evaluator view can show a profile image and display name inferred from the
sanitised persona background. These are fictional generative agents, not human
participants. Experimental condition labels remain hidden during rating to avoid
biasing judgements. Known profiles use existing persona image assets from the
Generative Agents environment; unmatched future profiles fall back to a neutral
generated-agent avatar derived from the blinded agent ID.

## Structure

```text
agent_eval_react_site/
  src/
    assets/                 # UI kit images
    components/
      assetManifest.js       # Asset imports and metadata
      UiAssetComponents.jsx  # Reusable React components from the kit pattern
    App.jsx                  # Website composition
    styles.css               # Plain CSS implementation of the kit visual style
```

This is a separate website project. It does not change the Streamlit rating
workflow or write any rating CSV files.
