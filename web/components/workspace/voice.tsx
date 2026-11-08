"use client";
import { useEffect, useRef, useState } from "react";
import {
  useConversationClientTool,
  useConversationControls,
  useConversationInput,
  useConversationMode,
  useConversationStatus,
} from "@elevenlabs/react";
import { Mic, MicOff, Square } from "lucide-react";
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
  const { isMuted, setMuted } = useConversationInput();
  const [preparing, setPreparing] = useState(false);
  const [starting, setStarting] = useState(false);
  const [consent, setConsent] = useState(false);
  const alive = useRef(true);
  const generation = useRef(0);
  const blocked = useRef(disabled);
  const limit = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const active = status === "connecting" || status === "connected";
  useConversationClientTool("daybreak_turn", async ({ message }) => {
    if (typeof message !== "string" || !message.trim())
      return JSON.stringify({
        error: "A message is required. No action was taken.",
      });
    try {
      setPreparing(true);
      const result = await turn(message);
      // Voice needs only the verified spoken reply. Keep evidence and UI objects in the app.
      return JSON.stringify({ reply: result.reply });
    } catch (error) {
      onError(error);
      return JSON.stringify({
        error:
          "The application did not confirm a result. Do not claim success. Please use the text interface.",
      });
    } finally {
      if (alive.current) setPreparing(false);
    }
  });
  useEffect(() => {
    alive.current = true;
    return () => {
      alive.current = false;
      generation.current += 1;
      endSession();
      clearTimeout(limit.current);
    };
  }, [endSession]);
  useEffect(() => {
    blocked.current = disabled;
    if (disabled) {
      generation.current += 1;
      endSession();
      clearTimeout(limit.current);
    }
  }, [disabled, endSession]);
  useEffect(() => {
    if (status === "error")
      onError(new Error("Voice is unavailable. Continue by typing below."));
  }, [status, onError]);
  async function start() {
    if (!consent || disabled || starting || active) return;
    const attempt = ++generation.current;
    const current = () => alive.current && !blocked.current && generation.current === attempt;
    setStarting(true);
    try {
      // Explicit consent precedes microphone capture and creation of a paid voice session.
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      if (!current()) return;
      const session = await api<SessionInfo>("conversation/voice-session", {
        scenario,
      });
      if (!current()) return;
      const signedUrl = session.signed_url ?? session.signedUrl;
      const conversationToken =
        session.conversation_token ?? session.conversationToken;
      setMuted(false);
      if (signedUrl) startSession({ signedUrl, connectionType: "websocket" });
      else if (conversationToken)
        startSession({ conversationToken, connectionType: "webrtc" });
      else
        throw new Error(
          "A private voice session could not be created. Continue by typing.",
        );
      if (!current()) {
        endSession();
        return;
      }
      clearTimeout(limit.current);
      limit.current = setTimeout(
        endSession,
        Math.min(session.max_duration_seconds ?? 600, 600) * 1000,
      );
    } catch (error) {
      if (current()) onError(error);
    } finally {
      if (alive.current) setStarting(false);
    }
  }
  return (
    <div className="db-voice">
      {!active && (
        <label className="db-consent">
          <input
            type="checkbox"
            checked={consent}
            disabled={starting}
            onChange={(e) => setConsent(e.target.checked)}
          />{" "}
          I agree to send my voice and this conversation to ElevenLabs.
        </label>
      )}
      <div className="db-voice-controls">
        <button
          type="button"
          className={active ? "db-button" : "db-primary"}
          disabled={disabled || starting || (!active && !consent)}
          onClick={() => {
            if (active) {
              generation.current += 1;
              endSession();
              clearTimeout(limit.current);
            } else void start();
          }}
        >
          {active ? <Square size={16} /> : <Mic size={16} />}
          {active ? "End voice" : starting ? "Connecting…" : "Talk to Daybreak"}
        </button>
        {status === "connected" && (
          <button
            type="button"
            className="db-button"
            aria-pressed={isMuted}
            onClick={() => setMuted(!isMuted)}
          >
            {isMuted ? <MicOff size={16} /> : <Mic size={16} />}
            {isMuted ? "Resume microphone" : "Mute microphone"}
          </button>
        )}
        <span role="status">
          {active
            ? status === "connecting"
              ? "Connecting…"
              : preparing
                ? "Preparing your answer…"
                : isSpeaking
                ? "Daybreak is speaking"
                : isMuted
                  ? "Microphone is muted"
                : "Listening"
            : "Start when safely stopped. Switch to Text any time."}
        </span>
      </div>
    </div>
  );
}
