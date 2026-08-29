import { useState } from 'react'
import { ThumbsDown, ThumbsUp } from 'lucide-react'
import { submitFeedback } from '../services/api'

const REASON_CHIPS = [
  { id: 'too_hard',     label: 'Too hard' },
  { id: 'too_easy',     label: 'Too easy' },
  { id: 'not_relevant', label: 'Not relevant' },
  { id: 'too_long',     label: 'Too long' },
  { id: 'great',        label: 'Great pick!' },
]

interface Props {
  itemId: string
  itemType: string
}

export default function FeedbackControl({ itemId, itemType }: Props) {
  const [rating, setRating] = useState<1 | -1 | null>(null)
  const [reason, setReason] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)

  async function handleRate(r: 1 | -1) {
    setRating(r)
    setReason(null) // reset chip when flipping
    if (r === 1) await save(r, null)   // thumbs-up → save immediately
  }

  async function handleReason(chip: string) {
    setReason(chip)
    await save(rating!, chip)
  }

  async function save(r: 1 | -1, chip: string | null) {
    setSaving(true)
    try {
      await submitFeedback(itemId, itemType, r, chip ?? undefined)
      setSaved(true)
    } catch { /* silent */ }
    finally { setSaving(false) }
  }

  if (saved) {
    return (
      <p className="text-xs font-medium text-slate-400">
        Thanks for the feedback!
      </p>
    )
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-xs text-slate-400">Helpful?</span>
      <button
        type="button"
        onClick={() => handleRate(1)}
        disabled={saving}
        className={`rounded-full p-1.5 transition ${
          rating === 1
            ? 'bg-emerald-100 text-emerald-600'
            : 'text-slate-400 hover:text-emerald-500'
        }`}
        aria-label="Thumbs up"
      >
        <ThumbsUp className="h-3.5 w-3.5" />
      </button>
      <button
        type="button"
        onClick={() => handleRate(-1)}
        disabled={saving}
        className={`rounded-full p-1.5 transition ${
          rating === -1
            ? 'bg-red-100 text-red-500'
            : 'text-slate-400 hover:text-red-400'
        }`}
        aria-label="Thumbs down"
      >
        <ThumbsDown className="h-3.5 w-3.5" />
      </button>

      {rating === -1 && !saved && (
        <div className="flex flex-wrap gap-1">
          {REASON_CHIPS.filter(c => c.id !== 'great').map(chip => (
            <button
              key={chip.id}
              type="button"
              onClick={() => handleReason(chip.id)}
              disabled={saving}
              className={`rounded-full border px-2.5 py-0.5 text-xs transition ${
                reason === chip.id
                  ? 'border-red-400 bg-red-50 text-red-700'
                  : 'border-slate-200 text-slate-500 hover:border-red-300'
              }`}
            >
              {chip.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
