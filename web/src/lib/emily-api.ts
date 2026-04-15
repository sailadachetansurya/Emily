/**
 * Emily Backend API Client
 *
 * Connects to the Python emotive pipeline at D:\dheer@j\Emily
 *
 * TODO: Start Emily pipeline as FastAPI server:
 *   cd D:\dheer@j\Emily
 *   .venv\Scripts\python -m uvicorn src.pipeline.api:app --reload
 */

export interface EmotionState {
  emotional_valence: number;
  activation_level: "low" | "medium" | "high";
  social_orientation: "withdrawn" | "neutral" | "reaching";
  stability: "stable" | "fragile" | "volatile";
  signals: Record<string, number>;
}

export interface EmilyRequest {
  request_id: string;
  user_id: string;
  user_input: string;
  trace_id: string;
  metadata?: Record<string, unknown>;
}

export interface EmilyResponse {
  request_id: string;
  response: {
    text: string;
    was_regenerated: boolean;
    safety_notes: string[];
  };
  traces: Array<{
    stage_name: string;
    status: string;
    metadata?: Record<string, unknown>;
  }>;
}

const EMILY_BASE_URL = process.env.EMILY_API_URL || "http://localhost:8000";

function pickByText(text: string, options: string[]): string {
  const seed = text.split("").reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  return options[seed % options.length];
}

function makeFallbackText(entry: string): string {
  const lower = entry.toLowerCase();
  if (lower.includes("sad") || lower.includes("down")) {
    return pickByText(entry, [
      "I hear sadness in this. I am here with you. What feels heaviest right now?",
      "This sounds painful, and you are not alone in it. Want to name one part first?",
      "I can feel the low energy in this. What helped even a little last time?",
    ]);
  }
  if (lower.includes("anx") || lower.includes("worry") || lower.includes("stress")) {
    return pickByText(entry, [
      "I hear stress building up. Want to unpack the biggest pressure first?",
      "That sounds tense and crowded in your mind. What is the loudest thought right now?",
      "This feels anxiety-heavy. Do you want a short grounding step or just space to vent?",
    ]);
  }
  return pickByText(entry, [
    "Thanks for sharing this. I am with you. What part do you want to focus on first?",
    "I hear you. Want to go step by step through this moment?",
    "That sounds like a lot to carry. What feels most present right now?",
  ]);
}

export class EmilyAPIClient {
  private userId: string;
  private lastResponseText: string | null = null;

  constructor(userId: string) {
    this.userId = userId;
  }

  async analyzeJournal(entry: string): Promise<EmilyResponse> {
    const request: EmilyRequest = {
      request_id: `req-${Date.now()}`,
      user_id: this.userId,
      user_input: entry,
      trace_id: `trace-${Date.now()}`,
    };

    try {
      const response = await fetch(`${EMILY_BASE_URL}/api/pipeline/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Emily API error: ${response.status}`);
      }

      const parsed = (await response.json()) as EmilyResponse;
      if (parsed.response?.text === this.lastResponseText) {
        const followUp = pickByText(entry, [
          "What part of this feels hardest right now?",
          "What do you need most in this moment?",
          "Do you want to vent more or pause and breathe?",
        ]);
        parsed.response.text = `${parsed.response.text} ${followUp}`;
      }
      this.lastResponseText = parsed.response?.text ?? null;
      return parsed;
    } catch (error) {
      console.error("Emily API call failed:", error);
      const fallbackText = makeFallbackText(entry);
      this.lastResponseText = fallbackText;
      return {
        request_id: request.request_id,
        response: {
          text: fallbackText,
          was_regenerated: false,
          safety_notes: ["fallback_mode"],
        },
        traces: [{ stage_name: "fallback", status: "ok" }],
      };
    }
  }

  async getEmotionState(entry: string): Promise<EmotionState> {
    const response = await this.analyzeJournal(entry);

    // Extract emotion from traces (emotion_perception stage)
    const emotionTrace = response.traces.find(
      (t) => t.stage_name === "emotion_perception"
    );

    if (emotionTrace?.metadata?.emotion) {
      return emotionTrace.metadata.emotion as EmotionState;
    }

    // Default neutral state
    return {
      emotional_valence: 0,
      activation_level: "medium",
      social_orientation: "neutral",
      stability: "stable",
      signals: {},
    };
  }

  async getInsights(userId: string): Promise<Insight[]> {
    // TODO: Implement when Emily backend supports insights endpoint
    return [
      {
        id: "insight-1",
        type: "pattern",
        message: "Your anxiety peaks on Sunday nights. Consider a wind-down routine.",
        severity: "medium",
        color: "orange",
      },
      {
        id: "insight-2",
        type: "positive",
        message: "You feel most energized after creative activities.",
        severity: "low",
        color: "green",
      },
    ];
  }
}

export interface Insight {
  id: string;
  type: "pattern" | "positive" | "warning" | "trigger";
  message: string;
  severity: "low" | "medium" | "high";
  color: "violet" | "green" | "orange" | "pink";
}

// Cache one client per user to keep sessions separated
const clientByUser = new Map<string, EmilyAPIClient>();

export function getEmilyClient(userId: string = "default-user"): EmilyAPIClient {
  const existing = clientByUser.get(userId);
  if (existing) return existing;

  const next = new EmilyAPIClient(userId);
  clientByUser.set(userId, next);
  return next;
}
