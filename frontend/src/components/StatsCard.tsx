import { useStore } from '../store'

export default function StatsCard() {
  const stats = useStore(s => s.memoryStats)
  if (!stats) return <div style={{ fontSize: 12, color: '#7a7874' }}>加载中...</div>
  return (
    <div style={{ background: '#f3f0eb', borderRadius: 16, padding: 12 }}>
      <div style={{ fontWeight: 500, fontSize: 12, color: '#7a7874', marginBottom: 4 }}>记忆统计</div>
      <div style={{ fontSize: 14, color: '#2c2c2a' }}>{stats.total} 条记忆</div>
      <div style={{ fontSize: 12, color: '#7a7874', marginTop: 4 }}>平均重要度: {stats.avg_importance.toFixed(2)}</div>
    </div>
  )
}
