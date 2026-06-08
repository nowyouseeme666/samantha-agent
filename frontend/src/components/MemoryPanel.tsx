import { useStore } from '../store'

export default function MemoryPanel() {
  const stats = useStore(s => s.memoryStats)
  return (
    <div style={{ background: '#f3f0eb', borderRadius: 16, padding: 16 }}>
      <div style={{ fontSize: 12, fontWeight: 500, color: '#7a7874', marginBottom: 8 }}>记忆</div>
      {!stats || stats.total === 0 ? (
        <div style={{ fontSize: 14, color: '#7a7874', textAlign: 'center', padding: 12 }}>暂无相关记忆</div>
      ) : (
        <div style={{ fontSize: 14, color: '#2c2c2a' }}>已存储 {stats.total} 条记忆</div>
      )}
    </div>
  )
}
