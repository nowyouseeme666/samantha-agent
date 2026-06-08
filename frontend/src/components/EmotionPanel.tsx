import { useStore } from '../store'

export default function EmotionPanel() {
  const emotion = useStore(s => s.emotionState)
  const hasData = !!emotion?.label
  const opacity = hasData ? 1 : 0.5
  const v = emotion?.valence ?? 0
  const a = emotion?.arousal ?? 0
  const colors: Record<string,string> = { happy: '#a8c97e', sad: '#8fa4c4', angry: '#c48b7a', anxious: '#d4a574', tired: '#b8b0a8', neutral: '#dcc4a8' }
  return (
    <div style={{ background: '#f3f0eb', borderRadius: 16, padding: 16, opacity }}>
      <div style={{ fontSize: 12, fontWeight: 500, color: '#7a7874', marginBottom: 8 }}>情绪</div>
      <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 4, color: colors[emotion?.label || ''] || '#dcc4a8' }}>{emotion?.label || 'neutral'}</div>
      <div style={{ fontSize: 12, color: '#7a7874', marginBottom: 8 }}>Valence: {(v*100).toFixed(0)}%</div>
      <div style={{ height: 6, borderRadius: 3, background: '#e8e4dc', marginBottom: 12, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${((v+1)/2*100)}%`, backgroundColor: v >= 0 ? '#a8c97e' : '#c48b7a', borderRadius: 3, transition: 'width 0.4s ease-out' }} />
      </div>
      <div style={{ fontSize: 12, color: '#7a7874' }}>Arousal: {(a*100).toFixed(0)}%</div>
      <div style={{ height: 6, borderRadius: 3, background: '#e8e4dc', marginTop: 4, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${(a*100)}%`, background: '#c4956a', borderRadius: 3, transition: 'width 0.4s ease-out' }} />
      </div>
    </div>
  )
}
