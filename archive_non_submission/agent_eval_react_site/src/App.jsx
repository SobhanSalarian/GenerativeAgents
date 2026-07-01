import React, { useEffect, useMemo, useState } from "react";
import { BrandHeader } from "./components/UiAssetComponents.jsx";
import { uiAssets } from "./components/assetManifest.js";

const FIELDNAMES = [
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
];

const RATER_CODES = ["R1", "R2", "R3", "R4", "R5"];

const RUBRICS = [
  {
    key: "behavioural_consistency",
    title: "Behavioural consistency",
    question: "Does the agent act in line with persona and prior behaviour?",
    low: "1 = Contradicts persona",
    high: "5 = Fully consistent",
  },
  {
    key: "memory_coherence",
    title: "Memory coherence",
    question: "Does the agent use prior interaction history appropriately?",
    low: "1 = Ignores / misuses memory",
    high: "5 = Uses it well",
  },
  {
    key: "planning_plausibility",
    title: "Planning plausibility",
    question: "Does the stated plan connect logically to the decision?",
    low: "1 = No connection",
    high: "5 = Clear logical connection",
  },
  {
    key: "response_naturalness",
    title: "Response naturalness",
    question: "Does the reasoning read like a believable human response?",
    low: "1 = Clearly robotic / templated",
    high: "5 = Natural",
  },
];

const SCENARIOS = [
  {
    id: "commons-dilemma",
    title: "Commons Dilemma",
    status: "Shared resource management",
    summary:
      "Agents independently request credits from a finite shared community fund. The scenario tests whether individual restraint can support a sustainable group outcome.",
    raterFocus:
      "Look for whether the decision follows the agent's persona, memory of previous resource rounds, fair-share context, and stated plan.",
    packetEvidence: ["resource level", "fair share", "requested amount", "memory of prior rounds"],
  },
  {
    id: "information-consensus",
    title: "Information Consensus",
    status: "Information aggregation",
    summary:
      "Agents choose between options using private and shared evidence. The scenario tests whether individually plausible reasoning can contribute to group convergence on the correct option.",
    raterFocus:
      "Look for whether the agent uses available signals, prior consensus history, and plan references coherently when explaining its choice.",
    packetEvidence: ["selected option", "group tally", "signal history", "consensus state"],
  },
  {
    id: "task-assignment",
    title: "Task Assignment",
    status: "Role allocation",
    summary:
      "Agents divide work across available tasks according to goals, capabilities, and local context. The scenario is useful for judging whether role choices are coherent and non-duplicative.",
    raterFocus:
      "Look for whether the agent's chosen role or task is consistent with its background, stated goals, and awareness of group needs.",
    packetEvidence: ["task choice", "role fit", "available tasks", "coordination notes"],
  },
  {
    id: "emergency-coordination",
    title: "Emergency Coordination",
    status: "Time-sensitive response",
    summary:
      "Agents respond to a simulated urgent event where coverage, prioritisation, and rapid coordination matter. The scenario tests decision plausibility under pressure.",
    raterFocus:
      "Look for whether the agent's response is credible given the emergency context, available information, and any plan or memory evidence.",
    packetEvidence: ["response action", "coverage need", "urgency", "coordination cue"],
  },
];

const EMPTY_FORM = {
  behavioural_consistency: 3,
  memory_coherence: 3,
  planning_plausibility: 3,
  response_naturalness: 3,
  believable_yes_no: "",
  notes: "",
};

const INFORMATION_CONSENSUS_OPTIONS = {
  A: "Shared creative studio and collaborative workshop space",
  B: "Community learning centre with digital skills programs",
  C: "Outdoor recreation area and wellness garden",
};

function displayValue(value) {
  if (value === null || value === undefined || value === "") {
    return "-- not available --";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  return String(value);
}

function hasValue(value) {
  return value !== null && value !== undefined && value !== "";
}

function isInformationConsensus(packet) {
  return packet?.scenario === "information_consensus";
}

function formatScenarioName(scenario) {
  if (!scenario) return "-- not available --";
  return String(scenario)
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function formatPercent(value) {
  if (!hasValue(value)) return value;
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return value;
  return `${Math.round(numeric * 100)}%`;
}

function formatVoteTally(value) {
  if (!value || typeof value !== "object") return value;
  return Object.entries(value)
    .map(([option, count]) => `${option}: ${count}`)
    .join(" | ");
}

function buildMetricItems(packet, localContext, macroState, decision) {
  const core = [
    ["Phase", packet.phase],
    ["Trial", packet.trial],
    ["Step", packet.step],
  ];

  if (isInformationConsensus(packet)) {
    return [
      ...core,
      ["Choice", decision.vote],
      ["Consensus rate", macroState.consensus_rate != null ? formatPercent(macroState.consensus_rate) : null],
      ["Coordinated", macroState.coordinated],
    ].filter(([, value]) => hasValue(value));
  }

  return [
    ...core,
    ["Requested", decision.requested],
    ["Granted", decision.granted],
    ["Coordinated", macroState.coordinated],
  ].filter(([, value]) => hasValue(value));
}

function selectPersonaAvatar(personaBackground = "") {
  const text = personaBackground.toLowerCase();
  return uiAssets.personaAvatars.find((avatar) =>
    avatar.keywords.some((keyword) => text.includes(keyword)),
  );
}

function parseJsonl(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      try {
        return JSON.parse(line);
      } catch (error) {
        throw new Error(`Invalid JSON on line ${index + 1}: ${error.message}`);
      }
    });
}

function csvEscape(value) {
  const text = String(value ?? "");
  if (/[",\n\r]/.test(text)) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

function rowsToCsv(rows) {
  const header = FIELDNAMES.join(",");
  const body = rows.map((row) => FIELDNAMES.map((field) => csvEscape(row[field])).join(","));
  return [header, ...body].join("\n");
}

function parseCsv(text) {
  const rows = [];
  let cell = "";
  let row = [];
  let inQuotes = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (char === '"' && inQuotes && next === '"') {
      cell += '"';
      index += 1;
    } else if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      row.push(cell);
      cell = "";
    } else if ((char === "\n" || char === "\r") && !inQuotes) {
      if (char === "\r" && next === "\n") index += 1;
      row.push(cell);
      rows.push(row);
      row = [];
      cell = "";
    } else {
      cell += char;
    }
  }
  if (cell || row.length) {
    row.push(cell);
    rows.push(row);
  }

  const [header = [], ...dataRows] = rows.filter((items) => items.some((item) => item !== ""));
  return dataRows.map((items) =>
    Object.fromEntries(header.map((field, index) => [field, items[index] ?? ""])),
  );
}

function downloadFile(filename, content, type = "text/csv;charset=utf-8") {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function storageKey(raterId, sourceName) {
  return `agent-eval-ratings:${raterId}:${sourceName || "packets"}`;
}

function ratingRowFromPacket(packet, raterId, form) {
  return {
    packet_id: packet.packet_id ?? "",
    blinded_agent_id: packet.blinded_agent_id ?? "",
    scenario: packet.scenario ?? "",
    trial: packet.trial ?? "",
    step: packet.step ?? "",
    phase: packet.phase ?? "",
    rater_id: raterId,
    behavioural_consistency: form.behavioural_consistency,
    memory_coherence: form.memory_coherence,
    planning_plausibility: form.planning_plausibility,
    response_naturalness: form.response_naturalness,
    believable_yes_no: form.believable_yes_no,
    notes: form.notes,
  };
}

function App() {
  const [packets, setPackets] = useState([]);
  const [sourceName, setSourceName] = useState("");
  const [raterId, setRaterId] = useState("R1");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [ratings, setRatings] = useState({});
  const [form, setForm] = useState(EMPTY_FORM);
  const [message, setMessage] = useState("");

  const currentPacket = packets[currentIndex] ?? null;
  const ratedCount = useMemo(() => Object.keys(ratings).length, [ratings]);
  const progress = packets.length ? Math.round((ratedCount / packets.length) * 100) : 0;

  useEffect(() => {
    if (!sourceName) return;
    const saved = localStorage.getItem(storageKey(raterId, sourceName));
    const parsed = saved ? JSON.parse(saved) : {};
    setRatings(parsed);
    setCurrentIndex(findFirstUnrated(packets, parsed));
  }, [raterId, sourceName, packets]);

  useEffect(() => {
    if (!sourceName) return;
    localStorage.setItem(storageKey(raterId, sourceName), JSON.stringify(ratings));
  }, [ratings, raterId, sourceName]);

  useEffect(() => {
    if (!currentPacket) {
      setForm(EMPTY_FORM);
      return;
    }
    const existing = ratings[currentPacket.packet_id];
    setForm(existing ? rowToForm(existing) : EMPTY_FORM);
  }, [currentPacket, ratings]);

  function findFirstUnrated(packetList, ratingMap) {
    const index = packetList.findIndex((packet) => !ratingMap[packet.packet_id]);
    return index === -1 ? packetList.length : index;
  }

  function rowToForm(row) {
    return {
      behavioural_consistency: Number(row.behavioural_consistency) || 3,
      memory_coherence: Number(row.memory_coherence) || 3,
      planning_plausibility: Number(row.planning_plausibility) || 3,
      response_naturalness: Number(row.response_naturalness) || 3,
      believable_yes_no: row.believable_yes_no || "",
      notes: row.notes || "",
    };
  }

  async function handlePacketUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    try {
      const text = await file.text();
      const packetList = parseJsonl(text);
      setPackets(packetList);
      setSourceName(file.name);
      setMessage(`${packetList.length} packets loaded from ${file.name}.`);
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function handleCsvUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    const rows = parseCsv(await file.text()).filter((row) => row.rater_id === raterId);
    const imported = Object.fromEntries(rows.map((row) => [row.packet_id, row]));
    setRatings((previous) => ({ ...previous, ...imported }));
    setMessage(`${rows.length} existing ratings imported for ${raterId}.`);
  }

  function saveCurrent({ moveNext = true } = {}) {
    if (!currentPacket) return;
    if (!form.believable_yes_no) {
      setMessage("Choose Yes or No for overall believability before saving.");
      return;
    }
    const row = ratingRowFromPacket(currentPacket, raterId, form);
    const nextRatings = { ...ratings, [currentPacket.packet_id]: row };
    setRatings(nextRatings);
    setMessage(`Saved ${currentPacket.packet_id}.`);
    if (moveNext) {
      const nextIndex = findNextUnrated(currentIndex + 1, nextRatings);
      setCurrentIndex(nextIndex);
    }
  }

  function findNextUnrated(startIndex, ratingMap) {
    for (let index = startIndex; index < packets.length; index += 1) {
      if (!ratingMap[packets[index].packet_id]) return index;
    }
    return Math.min(startIndex, packets.length);
  }

  function exportRatings() {
    const orderedRows = packets
      .map((packet) => ratings[packet.packet_id])
      .filter(Boolean);
    downloadFile("human_eval_ratings.csv", rowsToCsv(orderedRows));
  }

  function clearProgress() {
    if (!sourceName) return;
    localStorage.removeItem(storageKey(raterId, sourceName));
    setRatings({});
    setCurrentIndex(0);
    setMessage(`Cleared saved browser progress for ${raterId}.`);
  }

  return (
    <div className="app-shell" id="top">
      <BrandHeader />
      <main className="evaluator-main">
        {!packets.length ? (
          <StartScreen
            raterId={raterId}
            setRaterId={setRaterId}
            onPacketUpload={handlePacketUpload}
            message={message}
          />
        ) : (
          <EvaluatorScreen
            currentPacket={currentPacket}
            currentIndex={currentIndex}
            packets={packets}
            raterId={raterId}
            setRaterId={setRaterId}
            ratings={ratings}
            ratedCount={ratedCount}
            progress={progress}
            form={form}
            setForm={setForm}
            message={message}
            onPacketUpload={handlePacketUpload}
            onCsvUpload={handleCsvUpload}
            onSave={saveCurrent}
            onExport={exportRatings}
            onClear={clearProgress}
            onPrevious={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
            onSkip={() => setCurrentIndex(Math.min(packets.length, currentIndex + 1))}
            onJump={setCurrentIndex}
          />
        )}
      </main>
    </div>
  );
}

function StartScreen({ raterId, setRaterId, onPacketUpload, message }) {
  const [setupOpen, setSetupOpen] = useState(false);

  return (
    <>
      <section className="study-intro">
        <div>
          <p className="eyebrow">Blinded human evaluation</p>
          <h1>Rate agent decisions from evidence packets</h1>
          <p>
            Review one generated-agent decision at a time. Use the persona,
            context, memory, plan and reasoning shown in each packet to complete
            the rating form.
          </p>
        </div>
        <div className="study-summary">
          <strong>What you will do</strong>
          <span>Select rater code</span>
          <span>Open study packet file</span>
          <span>Rate each decision</span>
          <span>Export completed CSV</span>
        </div>
      </section>

      <section className="setup-card">
        <div>
          <p className="eyebrow">Begin evaluation</p>
          <h2>Start your assigned rating session</h2>
          <p>
            Select your researcher-assigned rater code, then open the packet file
            provided for this study. You will review one agent decision at a time,
            save each rating, and export the completed CSV at the end.
          </p>
          <div className="start-steps" aria-label="Evaluation steps">
            <span>1. Select rater code</span>
            <span>2. Open packet file</span>
            <span>3. Rate decisions</span>
            <span>4. Export CSV</span>
          </div>
          {!setupOpen && (
            <button
              className="primary-action start-evaluation-button"
              onClick={() => setSetupOpen(true)}
              type="button"
            >
              Start evaluation
            </button>
          )}
        </div>
        {setupOpen ? (
          <div className="setup-controls" id="evaluation-setup">
            <label>
              Assigned rater code
              <select value={raterId} onChange={(event) => setRaterId(event.target.value)}>
                {RATER_CODES.map((code) => (
                  <option key={code} value={code}>{code}</option>
                ))}
              </select>
            </label>
            <label>
              Study packet file
              <input type="file" accept=".jsonl,.txt,application/jsonl" onChange={onPacketUpload} />
            </label>
            <p className="field-help">
              Upload the `human_eval_packets.jsonl` file supplied by the researcher.
              Progress is saved locally in this browser until you export the CSV.
            </p>
            {message && <p className="status-message">{message}</p>}
          </div>
        ) : (
          <div className="setup-preview" aria-hidden="true">
            <strong>Ready when you are</strong>
            <p>
              The rater-code selector and study packet upload will appear after
              you start the evaluation.
            </p>
          </div>
        )}
      </section>

      <StudyContext />
    </>
  );
}

function StudyContext() {
  return (
    <section className="study-context">
      <details>
        <summary>Scenario context</summary>
        <div className="scenario-card-grid compact-scenarios">
          {SCENARIOS.map((scenario) => (
            <article className="scenario-card" id={scenario.id} key={scenario.id}>
              <div className="scenario-card-header">
                <span>{scenario.status}</span>
              </div>
              <h3>{scenario.title}</h3>
              <p>{scenario.summary}</p>
              <h4>Rater focus</h4>
              <p>{scenario.raterFocus}</p>
            </article>
          ))}
        </div>
      </details>
      <details>
        <summary>Rating rubric anchors</summary>
        <div className="dimension-grid compact-dimensions">
          {RUBRICS.map((dimension) => (
            <article className="dimension-card" key={dimension.key}>
              <h3>{dimension.title}</h3>
              <p>{dimension.question}</p>
              <span>{dimension.low}</span>
              <span>{dimension.high}</span>
            </article>
          ))}
        </div>
      </details>
    </section>
  );
}

function EvaluatorScreen(props) {
  const {
    currentPacket,
    currentIndex,
    packets,
    raterId,
    setRaterId,
    ratings,
    ratedCount,
    progress,
    form,
    setForm,
    message,
    onPacketUpload,
    onCsvUpload,
    onSave,
    onExport,
    onClear,
    onPrevious,
    onSkip,
    onJump,
  } = props;

  if (!currentPacket) {
    const firstUnratedIndex = packets.findIndex((packet) => !ratings[packet.packet_id]);
    const allRated = firstUnratedIndex === -1;
    return (
      <section className="complete-panel">
        <p className="eyebrow">{allRated ? "Complete" : "End reached"}</p>
        <h1>{allRated ? "All packets rated" : "Some packets are still unrated"}</h1>
        <p>
          {allRated
            ? "Export the completed CSV and send it back to the researcher."
            : "You reached the end of the packet list. Return to the first unrated packet or export the ratings completed so far."}
        </p>
        <div className="hero-actions">
          {!allRated && (
            <button className="secondary-action" onClick={() => onJump(firstUnratedIndex)}>
              Go to first unrated packet
            </button>
          )}
          <button className="primary-action" onClick={onExport}>
            Download human_eval_ratings.csv
          </button>
        </div>
      </section>
    );
  }

  const localContext = currentPacket.local_context ?? {};
  const macroState = localContext.macro_state ?? {};
  const decision = currentPacket.decision ?? {};
  const personaAvatar = selectPersonaAvatar(currentPacket.persona_background);
  const metricItems = buildMetricItems(currentPacket, localContext, macroState, decision);

  return (
    <div className="evaluator-grid">
      <aside className="control-panel">
        <p className="eyebrow">Session</p>
        <label>
          Rater code
          <select value={raterId} onChange={(event) => setRaterId(event.target.value)}>
            {RATER_CODES.map((code) => (
              <option key={code} value={code}>{code}</option>
            ))}
          </select>
        </label>
        <label>
          Load another packet file
          <input type="file" accept=".jsonl,.txt,application/jsonl" onChange={onPacketUpload} />
        </label>
        <label>
          Import existing ratings CSV
          <input type="file" accept=".csv,text/csv" onChange={onCsvUpload} />
        </label>
        <div className="score-progress">
          <span>Progress</span>
          <strong>{ratedCount} / {packets.length}</strong>
        </div>
        <div className="progress-track"><span style={{ width: `${progress}%` }} /></div>
        <button className="primary-action wide" onClick={onExport}>Download CSV</button>
        <button className="secondary-action wide" onClick={onClear}>Clear local progress</button>
        {message && <p className="status-message">{message}</p>}
        <div className="packet-list">
          {packets.map((packet, index) => (
            <button
              className={`${index === currentIndex ? "active" : ""} ${ratings[packet.packet_id] ? "rated" : ""}`}
              key={packet.packet_id}
              onClick={() => onJump(index)}
            >
              {index + 1}
            </button>
          ))}
        </div>
      </aside>

      <section className="packet-workspace">
        <header className="packet-title">
          <div className="packet-title-main">
            <AgentProfileImage avatar={personaAvatar} agentId={currentPacket.blinded_agent_id} />
            <div>
              <p className="eyebrow">Decision review</p>
              <h1>Packet {currentIndex + 1} of {packets.length}</h1>
              {personaAvatar && (
                <p className="agent-display-name">
                  {personaAvatar.name} <span>{personaAvatar.role}</span>
                </p>
              )}
            </div>
          </div>
          <strong>{displayValue(currentPacket.blinded_agent_id)}</strong>
        </header>

        {personaAvatar && (
          <div className="avatar-notice">
            <p className="eyebrow">Generative agent profile</p>
            <p>
              Profile image and name inferred from the generated agent's persona.
              Experimental condition labels remain hidden during rating.
            </p>
          </div>
        )}

        <div className="metric-grid">
          {metricItems.map(([label, value]) => (
            <Metric label={label} value={value} key={label} />
          ))}
        </div>

        <Panel title="Agent background">
          <TextBlock value={currentPacket.persona_background} />
        </Panel>

        <div className="two-column">
          <SituationPanel
            currentPacket={currentPacket}
            localContext={localContext}
            macroState={macroState}
          />
          <Panel title="Available memory and plan">
            <h3>Recent memories</h3>
            <BulletList items={localContext.recent_memories} />
            <h3>Daily goals</h3>
            <BulletList items={localContext.daily_goals} />
            <h3>Plan reference</h3>
            <TextBlock value={decision.plan_reference} />
          </Panel>
        </div>

        <DecisionPanel currentPacket={currentPacket} decision={decision} />
      </section>

      <section className="rating-panel">
        <p className="eyebrow">Ratings</p>
        {RUBRICS.map((rubric) => (
          <label className="rating-card" key={rubric.key}>
            <strong>{rubric.title}</strong>
            <span>{rubric.question}</span>
            <em>{rubric.low}</em>
            <em>{rubric.high}</em>
            <input
              type="range"
              min="1"
              max="5"
              value={form[rubric.key]}
              onChange={(event) => setForm({ ...form, [rubric.key]: Number(event.target.value) })}
            />
            <b>Current: {form[rubric.key]}</b>
          </label>
        ))}

        <fieldset className="believability">
          <legend>Would a naive reader believe this agent is human?</legend>
          <label>
            <input
              type="radio"
              name="believable"
              checked={form.believable_yes_no === "Yes"}
              onChange={() => setForm({ ...form, believable_yes_no: "Yes" })}
            />
            Yes
          </label>
          <label>
            <input
              type="radio"
              name="believable"
              checked={form.believable_yes_no === "No"}
              onChange={() => setForm({ ...form, believable_yes_no: "No" })}
            />
            No
          </label>
        </fieldset>

        <label className="notes-field">
          Notes
          <textarea
            value={form.notes}
            onChange={(event) => setForm({ ...form, notes: event.target.value })}
            placeholder="Optional comments"
          />
        </label>

        <div className="action-row">
          <button className="secondary-action" onClick={onPrevious} disabled={currentIndex === 0}>Previous</button>
          <button className="secondary-action" onClick={onSkip}>Skip</button>
          <button className="primary-action" onClick={() => onSave()}>Save & Next</button>
        </div>
      </section>
    </div>
  );
}

function SituationPanel({ currentPacket, localContext, macroState }) {
  if (isInformationConsensus(currentPacket)) {
    const facts = [
      ["Scenario", formatScenarioName(currentPacket.scenario)],
      ["Decision task", "Choose the best facility option from A, B, or C"],
      ["Vote tally", formatVoteTally(macroState.vote_tally)],
      ["Consensus rate", formatPercent(macroState.consensus_rate)],
      ["Consensus reached", macroState.consensus_reached],
      ["Information diffusion", formatPercent(macroState.information_diffusion_rate)],
      ["Coordinated this round", macroState.coordinated],
    ].filter(([, value]) => hasValue(value));

    return (
      <Panel title="Information consensus context">
        <dl className="facts-grid">
          {facts.map(([label, value]) => (
            <Fact label={label} value={value} key={label} />
          ))}
        </dl>
        <div className="option-list" aria-label="Facility options">
          {Object.entries(INFORMATION_CONSENSUS_OPTIONS).map(([option, description]) => (
            <p key={option}>
              <strong>Option {option}</strong>
              <span>{description}</span>
            </p>
          ))}
        </div>
      </Panel>
    );
  }

  const facts = [
    ["Resource before", localContext.resource_level_before],
    ["Pool percent before", localContext.pool_percent_before],
    ["Fair share", localContext.fair_share],
    ["Group total requested", macroState.total_requested],
    ["Resource note", macroState.resource_level_note],
    ["Current activity", localContext.current_activity],
  ].filter(([, value]) => hasValue(value));

  return (
    <Panel title="Situation">
      <dl className="facts-grid">
        {facts.map(([label, value]) => (
          <Fact label={label} value={value} key={label} />
        ))}
      </dl>
    </Panel>
  );
}

function DecisionPanel({ currentPacket, decision }) {
  if (isInformationConsensus(currentPacket)) {
    const facts = [
      ["Selected option", decision.vote],
      ["Previous option", decision.prior_vote],
      ["Changed position", decision.position_change],
      ["Signal disclosed", decision.signal_disclosed],
    ].filter(([, value]) => hasValue(value));

    return (
      <Panel title="Choice reasoning">
        {facts.length > 0 && (
          <dl className="facts-grid compact-facts">
            {facts.map(([label, value]) => (
              <Fact label={label} value={value} key={label} />
            ))}
          </dl>
        )}
        <TextBlock value={decision.reasoning} />
        {hasValue(decision.shared_statement) && (
          <>
            <h3>Statement shared with group</h3>
            <TextBlock value={decision.shared_statement} />
          </>
        )}
        <h3>Memory cited</h3>
        <TextBlock value={decision.memory_reference} />
      </Panel>
    );
  }

  return (
    <Panel title="Decision reasoning">
      <TextBlock value={decision.reasoning} />
      <h3>Memory cited</h3>
      <TextBlock value={decision.memory_reference} />
    </Panel>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric-card">
      <span>{label}</span>
      <strong>{displayValue(value)}</strong>
    </div>
  );
}

function AgentProfileImage({ avatar, agentId }) {
  if (avatar) {
    return (
      <img
        className="agent-profile-image"
        src={avatar.src}
        alt={`${avatar.name} profile`}
      />
    );
  }
  const suffix = displayValue(agentId).slice(-2).toUpperCase();
  return <div className="agent-profile-image fallback" aria-label="Generated agent profile">{suffix}</div>;
}

function Panel({ title, children }) {
  return (
    <article className="content-panel">
      <h2>{title}</h2>
      {children}
    </article>
  );
}

function TextBlock({ value }) {
  return <p className={displayValue(value) === "-- not available --" ? "empty-text" : "text-block"}>{displayValue(value)}</p>;
}

function BulletList({ items = [] }) {
  if (!items.length) return <p className="empty-text">-- not available --</p>;
  return (
    <ul className="evidence-list">
      {items.map((item, index) => <li key={`${item}-${index}`}>{displayValue(item)}</li>)}
    </ul>
  );
}

function Fact({ label, value }) {
  return (
    <div className="fact-card">
      <dt>{label}</dt>
      <dd>{displayValue(value)}</dd>
    </div>
  );
}

export default App;
