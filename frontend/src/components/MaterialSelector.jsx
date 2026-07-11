import React, { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  addMaterial,
  removeMaterial,
  addSample,
  removeSample,
} from "../redux/interactionSlice";
import { searchMaterials, searchSamples } from "../services/api";

function SearchDropdown({ placeholder, onSearch, onPick }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);

  const handleChange = async (e) => {
    const value = e.target.value;
    setQuery(value);
    if (value.length < 2) {
      setResults([]);
      return;
    }
    try {
      const { data } = await onSearch(value);
      setResults(data);
      setOpen(true);
    } catch {
      setResults([]);
    }
  };

  return (
    <div style={{ position: "relative" }}>
      <input
        type="text"
        placeholder={placeholder}
        value={query}
        onChange={handleChange}
        onFocus={() => results.length && setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
      />
      {open && results.length > 0 && (
        <div
          style={{
            position: "absolute",
            zIndex: 10,
            background: "#fff",
            border: "1px solid #e4e7ec",
            borderRadius: 8,
            width: "100%",
            marginTop: 4,
            boxShadow: "0 4px 12px rgba(16,24,40,0.08)",
          }}
        >
          {results.map((r) => (
            <div
              key={r.id}
              onMouseDown={() => {
                onPick(r);
                setQuery("");
                setResults([]);
                setOpen(false);
              }}
              style={{ padding: "8px 12px", cursor: "pointer", fontSize: 13 }}
            >
              {r.name}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function MaterialSelector() {
  const dispatch = useDispatch();
  const { materialsShared, samplesDistributed } = useSelector((s) => s.interaction.form);

  return (
    <div className="field">
      <label>Materials Shared</label>
      <SearchDropdown
        placeholder="Search materials..."
        onSearch={searchMaterials}
        onPick={(m) => dispatch(addMaterial({ id: m.id, name: m.name }))}
      />
      {materialsShared.length === 0 ? (
        <div className="empty-hint">No materials added.</div>
      ) : (
        <div className="chip-list">
          {materialsShared.map((m) => (
            <span className="chip" key={m.id}>
              {m.name}
              <button onClick={() => dispatch(removeMaterial(m.id))} aria-label={`Remove ${m.name}`}>
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <label style={{ marginTop: 16 }}>Samples Distributed</label>
      <SearchDropdown
        placeholder="Search samples..."
        onSearch={searchSamples}
        onPick={(s) =>
          dispatch(addSample({ sampleId: s.id, name: s.name, quantity: 1 }))
        }
      />
      {samplesDistributed.length === 0 ? (
        <div className="empty-hint">No samples added.</div>
      ) : (
        <div className="chip-list">
          {samplesDistributed.map((s) => (
            <span className="chip" key={s.sampleId}>
              {s.name} × {s.quantity}
              <button onClick={() => dispatch(removeSample(s.sampleId))} aria-label={`Remove ${s.name}`}>
                ×
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}