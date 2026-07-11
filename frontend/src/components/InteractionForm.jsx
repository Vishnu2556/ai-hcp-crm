import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { setField, submitInteractionForm, setHcp } from "../redux/interactionSlice";
import { searchHcps } from "../services/api";
import MaterialSelector from "./MaterialSelector";

const SENTIMENTS = [
  { value: "positive", label: "Positive", emoji: "🙂" },
  { value: "neutral", label: "Neutral", emoji: "😐" },
  { value: "negative", label: "Negative", emoji: "🙁" },
];

export default function InteractionForm() {
  const dispatch = useDispatch();
  const form = useSelector((s) => s.interaction.form);
  const status = useSelector((s) => s.interaction.status);
  const suggestedFollowUps = useSelector((s) => s.interaction.suggestedFollowUps);

  const [hcpResults, setHcpResults] = useState([]);
  const [hcpOpen, setHcpOpen] = useState(false);

  const handleHcpSearch = async (e) => {
    const value = e.target.value;
    dispatch(setField({ field: "hcpName", value }));
    if (value.length < 2) return setHcpResults([]);
    const { data } = await searchHcps(value);
    setHcpResults(data);
    setHcpOpen(true);
  };

  const canSubmit = form.hcpId && form.topicsDiscussed && status !== "saving";

  return (
    <div className="panel">
      <h2>Interaction Details</h2>

      <div className="field-row">
        <div className="field" style={{ position: "relative" }}>
          <label>HCP Name</label>
          <input
            type="text"
            placeholder="Search or select HCP..."
            value={form.hcpName}
            onChange={handleHcpSearch}
            onBlur={() => setTimeout(() => setHcpOpen(false), 150)}
          />
          {hcpOpen && hcpResults.length > 0 && (
            <div
              style={{
                position: "absolute", zIndex: 10, background: "#fff",
                border: "1px solid #e4e7ec", borderRadius: 8, width: "100%",
                marginTop: 4, boxShadow: "0 4px 12px rgba(16,24,40,0.08)",
              }}
            >
              {hcpResults.map((h) => (
                <div
                  key={h.id}
                  onMouseDown={() => {
                    dispatch(setHcp({ id: h.id, name: h.name }));
                    setHcpOpen(false);
                  }}
                  style={{ padding: "8px 12px", cursor: "pointer", fontSize: 13 }}
                >
                  {h.name} <span style={{ color: "#98a2b3" }}>· {h.specialty}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="field">
          <label>Interaction Type</label>
          <select
            value={form.interactionType}
            onChange={(e) => dispatch(setField({ field: "interactionType", value: e.target.value }))}
          >
            <option>Meeting</option>
            <option>Call</option>
            <option>Email</option>
            <option>Conference</option>
            <option>Virtual Meeting</option>
          </select>
        </div>
      </div>

      <div className="field-row">
        <div className="field">
          <label>Date</label>
          <input
            type="date"
            value={form.date}
            onChange={(e) => dispatch(setField({ field: "date", value: e.target.value }))}
          />
        </div>
        <div className="field">
          <label>Time</label>
          <input
            type="time"
            value={form.time}
            onChange={(e) => dispatch(setField({ field: "time", value: e.target.value }))}
          />
        </div>
      </div>

      <div className="field">
        <label>Attendees</label>
        <input type="text" placeholder="Enter names or search..." />
      </div>

      <div className="field">
        <label>Topics Discussed</label>
        <textarea
          placeholder="Enter key discussion points..."
          value={form.topicsDiscussed}
          onChange={(e) => dispatch(setField({ field: "topicsDiscussed", value: e.target.value }))}
        />
      </div>

      <MaterialSelector />

      <div className="field" style={{ marginTop: 16 }}>
        <label>Observed / Inferred HCP Sentiment</label>
        <div className="sentiment-group">
          {SENTIMENTS.map((s) => (
            <label className="sentiment-option" key={s.value}>
              <input
                type="radio"
                name="sentiment"
                checked={form.sentiment === s.value}
                onChange={() => dispatch(setField({ field: "sentiment", value: s.value }))}
              />
              {s.emoji} {s.label}
            </label>
          ))}
        </div>
      </div>

      <div className="field">
        <label>Outcomes</label>
        <textarea
          placeholder="Key outcomes or agreements..."
          value={form.outcomes}
          onChange={(e) => dispatch(setField({ field: "outcomes", value: e.target.value }))}
        />
      </div>

      <div className="field">
        <label>Follow-up Actions</label>
        <textarea
          placeholder="Enter next steps or tasks..."
          value={form.followUpActions}
          onChange={(e) => dispatch(setField({ field: "followUpActions", value: e.target.value }))}
        />
      </div>

      {suggestedFollowUps.length > 0 && (
        <div className="suggested-followups">
          <strong>AI Suggested Follow-ups:</strong>
          <ul>
            {suggestedFollowUps.map((f, idx) => (
              <li
                key={idx}
                onClick={() =>
                  dispatch(
                    setField({
                      field: "followUpActions",
                      value: form.followUpActions ? `${form.followUpActions}\n- ${f}` : `- ${f}`,
                    })
                  )
                }
              >
                {f}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div style={{ marginTop: 20, display: "flex", gap: 10 }}>
        <button
          className="btn btn-primary"
          disabled={!canSubmit}
          onClick={() => dispatch(submitInteractionForm())}
        >
          {status === "saving" ? "Saving..." : "Log Interaction"}
        </button>
        {status === "saved" && <span style={{ color: "#16a34a", fontSize: 13, alignSelf: "center" }}>Saved ✓</span>}
        {status === "error" && <span style={{ color: "#dc2626", fontSize: 13, alignSelf: "center" }}>Save failed</span>}
      </div>
    </div>
  );
}