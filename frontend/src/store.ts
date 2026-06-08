import { create } from 'zustand'
import type { Conversation, Message, MemoryStats, EmotionState } from './types'
import { api } from './api'
let _msgId = 0; const nextId = () => `msg_${Date.now()}_${++_msgId}`
interface State {
  userId: string; conversations: Conversation[]; currentConvId: string | null; messages: Message[]
  memoryStats: MemoryStats | null; emotionState: EmotionState | null; isLoading: boolean; statusText: string
  error: string | null
  setUserId: (id: string) => void; loadConversations: () => Promise<void>;
  loadConversation: (id: string) => Promise<void>; createConversation: () => Promise<string>;
  deleteConversation: (id: string) => Promise<void>; renameConversation: (id: string, title: string) => Promise<void>;
  loadMemoryStats: () => Promise<void>; loadEmotion: () => Promise<void>;
  sendMessage: (content: string) => AsyncGenerator<void>
}
export const useStore = create<State>((set, get) => ({
  userId: 'web_user_001', conversations: [], currentConvId: null, messages: [],
  memoryStats: null, emotionState: null, isLoading: false, statusText: '', error: null,
  setUserId: (id) => set({ userId: id }),
  loadConversations: async () => { const d = await api.getConversations(get().userId); set({ conversations: d.conversations, currentConvId: d.current_id }) },
  loadConversation: async (id) => { const d = await api.getConversation(get().userId, id); set({ currentConvId: id, messages: d.messages || [] }) },
  createConversation: async () => { const d = await api.createConversation(get().userId); await get().loadConversations(); await get().loadConversation(d.id); return d.id },
  deleteConversation: async (id) => { const { userId, currentConvId } = get(); const r = await api.deleteConversation(userId, id) as any; if (currentConvId === id) await get().loadConversation(r.current_id); await get().loadConversations() },
  renameConversation: async (id, title) => { await api.renameConversation(get().userId, id, title); await get().loadConversations() },
  loadMemoryStats: async () => { try { const s = await api.getMemoryStats(get().userId); set({ memoryStats: s }) } catch {} },
  loadEmotion: async () => { try { const e = await api.getEmotion(); set({ emotionState: e }) } catch {} },
  sendMessage: async function* (content) {
    const { userId, currentConvId, messages } = get()
    set({ isLoading: true, statusText: '', error: null })
    const uMsg: Message = { id: nextId(), role: 'user', content }
    set(s => ({ messages: [...s.messages, uMsg] }))
    const aId = nextId()
    let aMsg: Message = { id: aId, role: 'assistant', content: '' }
    let added = false
    try {
      const stream = api.sendMessage(userId, content, messages, currentConvId)
      for await (const ev of stream) {
        if (ev.type === 'status') { set({ statusText: ev.text || '' }) }
        else if (ev.type === 'emotion' && ev.state) { set({ emotionState: ev.state }) }
        else if (ev.type === 'token') {
          aMsg = { ...aMsg, content: aMsg.content + (ev.text || '') }
          if (!added) { added = true; set(s => ({ messages: [...s.messages, aMsg], isLoading: false, statusText: '' })) }
          else { set(s => { const msgs = [...s.messages]; const i = msgs.findIndex(m => m.id === aId); if (i >= 0) msgs[i] = aMsg; return { messages: msgs } }) }
        } else if (ev.type === 'reply') {
          aMsg = { ...aMsg, content: ev.text || aMsg.content }
          if (added) { set(s => { const msgs = [...s.messages]; const i = msgs.findIndex(m => m.id === aId); if (i >= 0) msgs[i] = aMsg; return { messages: msgs } }) }
        } else if (ev.type === 'blocked') {
          set(s => ({ messages: [...s.messages, { id: aId, role: 'assistant', content: ev.text || '' }], isLoading: false }))
          return
        } else if (ev.type === 'done') {
          if (ev.conversation_id) { set({ currentConvId: ev.conversation_id }) }
          get().loadConversations(); get().loadMemoryStats(); yield
        } else if (ev.type === 'error') { throw new Error(ev.text || 'Unknown error') }
      }
    } catch (e) {
      const errMsg = `Sorry, something went wrong: ${e instanceof Error ? e.message : 'Unknown error'}`
      if (!added) { set(s => ({ messages: [...s.messages, { id: aId, role: 'assistant', content: errMsg }], isLoading: false })) }
      else { set(s => { const msgs = [...s.messages]; const i = msgs.findIndex(m => m.id === aId); if (i >= 0) msgs[i] = { ...msgs[i], content: errMsg }; return { messages: msgs, isLoading: false } }) }
    }
  }
}))
