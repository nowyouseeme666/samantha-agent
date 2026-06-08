import { useState } from 'react'
import { useStore } from '../store'

export default function ConversationList() {
  const conversations = useStore(s => s.conversations)
  const currentId = useStore(s => s.currentConvId)
  const load = useStore(s => s.loadConversation)
  const create = useStore(s => s.createConversation)
  const remove = useStore(s => s.deleteConversation)
  const rename = useStore(s => s.renameConversation)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')

  const startEdit = (id: string, title: string) => { setEditingId(id); setEditTitle(title) }
  const confirmEdit = (id: string) => {
    if (editTitle.trim()) { rename(id, editTitle.trim()) }
    setEditingId(null); setEditTitle('')
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <button onClick={() => create()} style={{ width: '100%', padding: '8px 12px', borderRadius: 12, border: '1px dashed rgba(196,149,106,0.3)', background: 'transparent', color: '#c4956a', cursor: 'pointer', fontSize: 14 }}>+ 新对话</button>
      {conversations.map(c => (
        <div key={c.id} onClick={() => editingId !== c.id && load(c.id)}
          onDoubleClick={() => startEdit(c.id, c.title)}
          onContextMenu={e => { e.preventDefault(); if (confirm('确认删除该对话？')) remove(c.id) }}
          style={{ padding: '8px 12px', borderRadius: 12, cursor: 'pointer', background: c.id === currentId ? 'rgba(196,149,106,0.12)' : 'transparent', fontSize: 14, color: '#2c2c2a' }}>
          {editingId === c.id ? (
            <input value={editTitle}
              onChange={e => setEditTitle(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter') confirmEdit(c.id); if (e.key === 'Escape') setEditingId(null) }}
              onBlur={() => confirmEdit(c.id)}
              onClick={e => e.stopPropagation()}
              autoFocus
              style={{ width: '100%', background: 'white', border: '1px solid rgba(196,149,106,0.4)', borderRadius: 8, padding: '4px 8px', fontSize: 14, color: '#2c2c2a', outline: 'none' }} />
          ) : (
            c.title || '新对话'
          )}
        </div>
      ))}
    </div>
  )
}
