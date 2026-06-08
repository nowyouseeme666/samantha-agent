export interface Message { id?: string; role: 'user' | 'assistant'; content: string; image?: string }
export interface Conversation { id: string; title: string; created: string; message_count: number; is_active: boolean; messages?: Message[] }
export interface MemoryStats { total: number; emotion_distribution?: Record<string,number>; avg_importance: number }
export interface EmotionState { valence: number; arousal: number; label: string; confidence: number }
export interface SSEEvent { type: 'status'|'token'|'reply'|'done'|'error'|'blocked'|'emotion'|'memory'; text?: string; state?: EmotionState; entries?: string[]; conversation_id?: string }
