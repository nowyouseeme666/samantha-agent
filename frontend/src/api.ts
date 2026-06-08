import type { Conversation, Message, MemoryStats, EmotionState } from './types'
const BASE = '/api'
async function request<T>(url: string, opts?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${url}`, { ...opts, headers: { 'Content-Type': 'application/json', ...(opts?.headers || {}) } })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}
export const api = {
  async *sendMessage(userId: string, message: string, history: Message[], convId: string | null): AsyncGenerator<{type:string;text?:string;state?:EmotionState;entries?:string[];conversation_id?:string}> {
    const res = await fetch(`${BASE}/chat/${userId}`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, conversation_history: history, conversation_id: convId })
    })
    if (!res.ok) throw new Error(await res.text())
    const reader = res.body?.getReader()
    if (!reader) throw new Error('No response body')
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const d = line.slice(6)
          if (d === '[DONE]') return
          try { yield JSON.parse(d) } catch {}
        }
      }
    }
  },
  getConversations: (uid: string) => request<{conversations:Conversation[];current_id:string}>(`/conversations/${uid}`),
  getConversation: (uid: string, cid: string) => request<{messages:Message[]}>(`/conversations/${uid}/${cid}`),
  createConversation: (uid: string) => request<{id:string;title:string}>(`/conversations/${uid}`, { method: 'POST' }),
  deleteConversation: (uid: string, cid: string) => request(`/conversations/${uid}/${cid}`, { method: 'DELETE' }),
  renameConversation: (uid: string, cid: string, title: string) => request(`/conversations/${uid}/${cid}`, { method: 'PATCH', body: JSON.stringify({ title }) }),
  getMemoryStats: (uid: string) => request<MemoryStats>(`/memory/${uid}/stats`),
  getEmotion: () => request<EmotionState>('/emotion'),
}
