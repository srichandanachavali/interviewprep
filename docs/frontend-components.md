### frontend/components/VoiceRecorder.tsx
```typescript
'use client'
import { useState, useRef, useCallback } from 'react'
import { Mic, Square } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function VoiceRecorder({
  onTranscript, disabled
}: { onTranscript: (t: string) => void; disabled?: boolean }) {
  const [recording, setRecording] = useState(false)
  const [liveText, setLiveText] = useState('')
  const ref = useRef<SpeechRecognition | null>(null)

  const start = useCallback(() => {
    const SR = window.SpeechRecognition ?? window.webkitSpeechRecognition
    if (!SR) { alert('Voice not supported. Please type your answer.'); return }
    const r = new SR()
    r.continuous = true; r.interimResults = true; r.lang = 'en-IN'
    r.onresult = (e) => {
      let t = ''
      for (let i = 0; i < e.results.length; i++) t += e.results[i][0].transcript
      setLiveText(t)
    }
    r.start(); ref.current = r; setRecording(true)
  }, [])

  const stop = useCallback(() => {
    ref.current?.stop(); ref.current = null
    setRecording(false); onTranscript(liveText)
  }, [liveText, onTranscript])

  return (
    <div className="space-y-2">
      {!recording
        ? <Button onClick={start} disabled={disabled} className="gap-2 bg-red-500 hover:bg-red-600">
            <Mic className="w-4 h-4" /> Speak Answer
          </Button>
        : <Button onClick={stop} variant="outline" className="gap-2 animate-pulse">
            <Square className="w-4 h-4 fill-current" /> Stop & Score
          </Button>
      }
      {recording && liveText && (
        <p className="text-sm italic text-muted-foreground bg-muted p-2 rounded">"{liveText}"</p>
      )}
    </div>
  )
}
```

### frontend/components/STARScoreCard.tsx
```typescript
import { STARScore } from '@/lib/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'

const WEAKNESS_LABELS: Record<string, string> = {
  missing_result: '⚠ No Result', missing_situation: '⚠ No Context',
  over_explains: '⚠ Too Wordy', no_quantified_impact: '⚠ No Numbers',
  too_vague: '⚠ Too Vague', rambling: '⚠ Unfocused',
  no_technical_depth: '⚠ Needs Depth', missing_action: '⚠ No Action',
}

export default function STARScoreCard({ score }: { score: STARScore }) {
  const color = score.total >= 75 ? 'text-green-600' : score.total >= 50 ? 'text-yellow-600' : 'text-red-600'
  return (
    <Card className="mt-4">
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>STAR Score</CardTitle>
          <span className={`text-3xl font-bold ${color}`}>{score.total}/100</span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          {(['situation','task','action','result'] as const).map(k => (
            <div key={k} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span className="capitalize font-medium">{k}</span>
                <span className="text-muted-foreground">{score[k]}/25</span>
              </div>
              <Progress value={(score[k] / 25) * 100} className="h-1.5" />
            </div>
          ))}
        </div>
        {score.weakness_tags.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {score.weakness_tags.map(t => (
              <Badge key={t} variant="destructive" className="text-xs">
                {WEAKNESS_LABELS[t] ?? t}
              </Badge>
            ))}
          </div>
        )}
        <div className="bg-muted rounded-lg p-3 text-sm space-y-1">
          <p className="font-medium">📝 Feedback</p>
          <p className="text-muted-foreground">{score.feedback}</p>
        </div>
        <details>
          <summary className="text-sm font-medium text-primary cursor-pointer hover:underline">
            ✨ See ideal answer
          </summary>
          <div className="mt-2 bg-green-50 dark:bg-green-950 rounded p-3 text-sm">
            {score.ideal_answer}
          </div>
        </details>
      </CardContent>
    </Card>
  )
}
```

### frontend/components/RapidFireTimer.tsx
```typescript
'use client'
import { useEffect, useState } from 'react'

export default function RapidFireTimer({
  totalSeconds, onTimeUp, isRunning
}: { totalSeconds: number; onTimeUp: () => void; isRunning: boolean }) {
  const [left, setLeft] = useState(totalSeconds)
  useEffect(() => { setLeft(totalSeconds) }, [totalSeconds])
  useEffect(() => {
    if (!isRunning || left <= 0) { if (left <= 0) onTimeUp(); return }
    const t = setTimeout(() => setLeft(l => l - 1), 1000)
    return () => clearTimeout(t)
  }, [left, isRunning, onTimeUp])
  const pct = (left / totalSeconds) * 100
  const c = pct > 50 ? '#22c55e' : pct > 25 ? '#f59e0b' : '#ef4444'
  return (
    <div className="flex items-center gap-2">
      <div className="relative w-14 h-14 rounded-full flex items-center justify-center"
        style={{ background: `conic-gradient(${c} ${pct*3.6}deg, #e5e7eb ${pct*3.6}deg)` }}>
        <div className="w-10 h-10 bg-background rounded-full flex items-center justify-center">
          <span className="text-base font-bold tabular-nums">{left}</span>
        </div>
      </div>
      <span className="text-xs text-muted-foreground">sec left</span>
    </div>
  )
}
```

