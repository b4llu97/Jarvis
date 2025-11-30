const ORCHESTRATOR_URL = import.meta.env.VITE_ORCHESTRATOR_URL || 'http://localhost:8003';
const ASR_URL = import.meta.env.VITE_ASR_URL || 'http://localhost:8004';
const TTS_URL = import.meta.env.VITE_TTS_URL || 'http://localhost:8005';
const TOOLSERVER_URL = import.meta.env.VITE_TOOLSERVER_URL || 'http://localhost:8002';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface QueryResponse {
  response: string;
  tool_calls: Array<{
    tool: string;
    args: Record<string, unknown>;
  }>;
  tool_results: Array<{
    tool: string;
    result: unknown;
  }>;
}

export interface TranscriptionResponse {
  text: string;
  language: string;
  duration?: number;
}

export async function sendTextQuery(query: string, history: Message[] = []): Promise<QueryResponse> {
  const response = await fetch(`${ORCHESTRATOR_URL}/v1/query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      conversation_history: history,
    }),
  });

  if (!response.ok) {
    throw new Error(`Orchestrator error: ${response.statusText}`);
  }

  return response.json();
}

export async function transcribeAudio(audioBlob: Blob): Promise<TranscriptionResponse> {
  const formData = new FormData();
  formData.append('file', audioBlob, 'audio.webm');

  const response = await fetch(`${ASR_URL}/v1/transcribe`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`ASR error: ${response.statusText}`);
  }

  return response.json();
}

export async function synthesizeSpeech(text: string): Promise<Blob> {
  const response = await fetch(`${TTS_URL}/v1/speak`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      text,
      speed: 1.0,
    }),
  });

  if (!response.ok) {
    throw new Error(`TTS error: ${response.statusText}`);
  }

  return response.blob();
}

export interface Fact {
  key: string;
  value: string;
  created_at?: string;
  updated_at?: string;
}

export async function listFacts(): Promise<Fact[]> {
  const response = await fetch(`${TOOLSERVER_URL}/v1/facts`);
  
  if (!response.ok) {
    throw new Error(`Toolserver error: ${response.statusText}`);
  }
  
  return response.json();
}

export async function getFact(key: string): Promise<Fact> {
  const response = await fetch(`${TOOLSERVER_URL}/v1/facts/${encodeURIComponent(key)}`);
  
  if (!response.ok) {
    throw new Error(`Toolserver error: ${response.statusText}`);
  }
  
  return response.json();
}

export async function setFact(key: string, value: string): Promise<Fact> {
  const response = await fetch(`${TOOLSERVER_URL}/v1/facts/${encodeURIComponent(key)}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ value }),
  });
  
  if (!response.ok) {
    throw new Error(`Toolserver error: ${response.statusText}`);
  }
  
  return response.json();
}

export async function deleteFact(key: string): Promise<void> {
  const response = await fetch(`${TOOLSERVER_URL}/v1/facts/${encodeURIComponent(key)}`, {
    method: 'DELETE',
  });
  
  if (!response.ok) {
    throw new Error(`Toolserver error: ${response.statusText}`);
  }
}

// Feedback & Learning API

export interface FeedbackRequest {
  query: string;
  response: string;
  rating: number;
  comment?: string;
  model?: string;
  provider?: string;
}

export interface CorrectionRequest {
  query: string;
  wrong_response: string;
  correct_response: string;
  context?: string;
}

export interface LearningStatistics {
  total_feedback: number;
  average_rating: number;
  rating_distribution: Record<number, number>;
  total_corrections: number;
  recent_feedback_7d: number;
}

export async function submitFeedback(feedback: FeedbackRequest): Promise<void> {
  const response = await fetch(`${TOOLSERVER_URL}/v1/feedback`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(feedback),
  });

  if (!response.ok) {
    throw new Error(`Feedback submission error: ${response.statusText}`);
  }
}

export async function submitCorrection(correction: CorrectionRequest): Promise<void> {
  const response = await fetch(`${TOOLSERVER_URL}/v1/corrections`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(correction),
  });

  if (!response.ok) {
    throw new Error(`Correction submission error: ${response.statusText}`);
  }
}

export async function getLearningStatistics(): Promise<LearningStatistics> {
  const response = await fetch(`${TOOLSERVER_URL}/v1/learning/statistics`);

  if (!response.ok) {
    throw new Error(`Statistics error: ${response.statusText}`);
  }

  return response.json();
}
