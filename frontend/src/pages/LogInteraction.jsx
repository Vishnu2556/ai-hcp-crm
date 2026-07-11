import React from "react";
import InteractionForm from "../components/InteractionForm";
import ChatPanel from "../components/ChatPanel";

export default function LogInteraction() {
  return (
    <div className="log-page">
      <h1 className="page-title">Log HCP Interaction</h1>

      <div className="log-interaction-page">
        <InteractionForm />
        <ChatPanel />
      </div>
    </div>
  );
}