import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import api from "../services/api";

const initialState = {
  form: {
    hcpId: null,
    hcpName: "",
    interactionType: "Meeting",
    date: new Date().toISOString().slice(0, 10),
    time: new Date().toTimeString().slice(0, 5),
    attendees: [],
    topicsDiscussed: "",
    materialsShared: [],   // [{id, name}]
    samplesDistributed: [], // [{sampleId, name, quantity}]
    sentiment: "neutral",
    outcomes: "",
    followUpActions: "",
  },
  suggestedFollowUps: [],
  chat: {
    sessionId: `session_${Date.now()}`,
    messages: [
      {
        role: "assistant",
        text: 'Log interaction details here (e.g., "Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure") or ask for help.',
      },
    ],
    isSending: false,
  },
  status: "idle", // idle | saving | saved | error
  lastSavedInteractionId: null,
  error: null,
};

export const submitInteractionForm = createAsyncThunk(
  "interaction/submitForm",
  async (_, { getState, rejectWithValue }) => {
    const { form } = getState().interaction;
    try {
      const payload = {
        hcp_id: form.hcpId,
        interaction_type: form.interactionType,
        interaction_date: `${form.date}T${form.time}:00`,
        attendee_ids: form.attendees.map((a) => a.id),
        topics_discussed: form.topicsDiscussed,
        material_ids: form.materialsShared.map((m) => m.id),
        samples: form.samplesDistributed.map((s) => ({
          sample_id: s.sampleId,
          quantity: s.quantity,
        })),
        sentiment: form.sentiment,
        outcomes: form.outcomes,
        follow_up_actions: form.followUpActions,
      };
      const { data } = await api.post("/api/interactions", payload);
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || "Failed to save interaction");
    }
  }
);

export const sendChatMessage = createAsyncThunk(
  "interaction/sendChatMessage",
  async (message, { getState, rejectWithValue }) => {
    const { sessionId } = getState().interaction.chat;
    try {
      const { data } = await api.post("/api/ai/chat", {
        session_id: sessionId,
        message,
      });
      return data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || "AI assistant is unavailable");
    }
  }
);

const interactionSlice = createSlice({
  name: "interaction",
  initialState,
  reducers: {
    setField(state, action) {
      const { field, value } = action.payload;
      state.form[field] = value;
    },
    setHcp(state, action) {
      state.form.hcpId = action.payload.id;
      state.form.hcpName = action.payload.name;
    },
    addMaterial(state, action) {
      if (!state.form.materialsShared.find((m) => m.id === action.payload.id)) {
        state.form.materialsShared.push(action.payload);
      }
    },
    removeMaterial(state, action) {
      state.form.materialsShared = state.form.materialsShared.filter(
        (m) => m.id !== action.payload
      );
    },
    addSample(state, action) {
      state.form.samplesDistributed.push(action.payload);
    },
    removeSample(state, action) {
      state.form.samplesDistributed = state.form.samplesDistributed.filter(
        (s) => s.sampleId !== action.payload
      );
    },
    resetForm(state) {
      state.form = initialState.form;
      state.suggestedFollowUps = [];
      state.status = "idle";
    },
    addUserChatMessage(state, action) {
      state.chat.messages.push({ role: "user", text: action.payload });
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(submitInteractionForm.pending, (state) => {
        state.status = "saving";
        state.error = null;
      })
      .addCase(submitInteractionForm.fulfilled, (state, action) => {
        state.status = "saved";
        state.lastSavedInteractionId = action.payload.id;
      })
      .addCase(submitInteractionForm.rejected, (state, action) => {
        state.status = "error";
        state.error = action.payload;
      })
      .addCase(sendChatMessage.pending, (state) => {
        state.chat.isSending = true;
      })
      .addCase(sendChatMessage.fulfilled, (state, action) => {
        state.chat.isSending = false;
        state.chat.messages.push({ role: "assistant", text: action.payload.reply });
        if (action.payload.suggested_follow_ups?.length) {
          state.suggestedFollowUps = action.payload.suggested_follow_ups;
        }
        // Sync form fields when the agent logged/edited an interaction via chat
        const i = action.payload.interaction;
        if (i) {
          state.form.hcpId = i.hcp_id;
          state.form.hcpName = i.hcp_name || state.form.hcpName;
          state.form.interactionType = i.interaction_type;
          state.form.topicsDiscussed = i.topics_discussed || "";
          state.form.outcomes = i.outcomes || "";
          state.form.followUpActions = i.follow_up_actions || "";
          state.form.sentiment = i.sentiment;
          state.form.materialsShared = i.materials_shared.map((m) => ({ id: m.id, name: m.name }));
          state.form.samplesDistributed = i.samples.map((s) => ({
            sampleId: s.sample_id,
            name: s.name,
            quantity: s.quantity,
          }));
          state.lastSavedInteractionId = i.id;
        }
      })
      .addCase(sendChatMessage.rejected, (state, action) => {
        state.chat.isSending = false;
        state.chat.messages.push({
          role: "assistant",
          text: `Sorry, something went wrong: ${action.payload}`,
        });
      });
  },
});

export const {
  setField,
  setHcp,
  addMaterial,
  removeMaterial,
  addSample,
  removeSample,
  resetForm,
  addUserChatMessage,
} = interactionSlice.actions;

export default interactionSlice.reducer;