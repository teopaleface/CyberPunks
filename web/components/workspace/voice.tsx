"use client";
import { useEffect, useRef, useState } from "react";
import {
  useConversationClientTool,
  useConversationControls,
  useConversationMode,
  useConversationStatus,
} from "@elevenlabs/react";
import { Mic, Square } from "lucide-react";
import { api } from "@/lib/operations/client";
import type { Turn } from "@/lib/operations/types";
interface SessionInfo {
  signed_url?: string;
  signedUrl?: string;
  conversation_token?: string;
  conversationToken?: string;
  max_duration_seconds?: number;
}
export function Voice({
  scenario,
  turn,
  onError,
  disabled,
}: {
  scenario: string;
  turn: (message: string) => Promise<Turn>;
  onError: (error: unknown) => void;
  disabled: boolean;
}) {
  const { startSession, endSession } = useConversationControls();
  const { status } = useConversationStatus();
  const { isSpeaking } = useConversationMode();
  const [starting, setStarting] = useState(false);
  const [consent, setConsent] = useState(false);
  const alive = useRef(true);
  const limit = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const active = status === "connecting" || status === "connected";
  useConversationClientTool("daybreak_turn", async ({ message }) => {
    if (typeof message !== "string" || !message.trim())
      return JSON.stringify({
        error: "A message is required. No action was taken.",
      });
    try {
      return JSON.stringify(await turn(message));
    } catch (error) {
      onError(error);
      return JSON.stringify({
        error:
          "The application did not confirm a result. Do not claim success. Please use the text interface.",
      });
    }
  });
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      endSession();
      clearTimeout(limit.current);
    };
  }, [endSession]);
  useEffect(() => {
    if (disabled) endSession();
  }, [disabled, endSession]);
  useEffect(() => {
    if (status === "error")
      onError(new Error("Voice is unavailable. Continue by typing below."));
  }, [status, onError]);
  async function start() {
    setStarting(true);
    try {
      // Explicit consent precedes microphone capture and creation of a paid voice session.
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      if (!alive.current) return;
      const session = await api<SessionInfo>("conversation/voice-session", {
        scenario,
      });
      if (!alive.current) return;
      const signedUrl = session.signed_url ?? session.signedUrl;
      const conversationToken =
        session.conversation_token ?? session.conversationToken;
      if (signedUrl) startSession({ signedUrl, connectionType: "websocket" });
      else if (conversationToken)
        startSession({ conversationToken, connectionType: "webrtc" });
      else
        throw new Error(
          "A private voice session could not be created. Continue by typing.",
        );
      clearTimeout(limit.current);
      limit.current = setTimeout(
        endSession,
        Math.min(session.max_duration_seconds ?? 300, 300) * 1000,
      );
    } catch (error) {
      onError(error);
    } finally {
      setStarting(false);
    }
  }
  return (
    <div className="db-voice">
      {!active && (
        <label className="db-consent">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
          />{" "}
          I agree to send this synthetic demo conversation and audio to
          ElevenLabs. Use voice only when safely stopped.
        </label>
      )}
      <div className="db-voice-controls">
        <button
          type="button"
          className={active ? "db-button" : "db-primary"}
          disabled={disabled || starting || (!active && !consent)}
          onClick={() => {
            if (active) {
              endSession();
              clearTimeout(limit.current);
            } else void start();
          }}
        >
          {active ? <Square size={16} /> : <Mic size={16} />}
          {active ? "End voice" : starting ? "Connecting…" : "Talk to Daybreak"}
        </button>
        <span role="status">
          {active
            ? status === "connecting"
              ? "Connecting…"
              : isSpeaking
                ? "Daybreak is speaking"
                : "Listening"
            : "Type instead, any time"}
        </span>
      </div>
    </div>
  );
}
