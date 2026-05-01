import { useState } from 'react'
import { Check, X } from 'lucide-react'
import { editItem } from '../api/items'

function unitLabel(unit: string): string {
  if (unit === 'g') return 'grams'
  if (unit === 'ml') return 'ml'
  return 'count'
}

interface Props {
  productReferenceId: string
  location: string
  currentName: string
  currentQty: number
  unit: string
  onClose: () => void
}

export default function EditItemModal({ productReferenceId, location, currentName, currentQty, unit, onClose }: Props) {
  const [name, setName] = useState(currentName)
  const [qtyStr, setQtyStr] = useState(String(currentQty % 1 === 0 ? currentQty : currentQty.toFixed(1)))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const qty = parseFloat(qtyStr)
  const nameChanged = name.trim() !== currentName
  const qtyChanged = !isNaN(qty) && qty > 0 && qty !== currentQty
  const canSave = (nameChanged || qtyChanged) && name.trim().length > 0 && !isNaN(qty) && qty > 0

  async function handleSave() {
    if (!canSave || saving) return
    setSaving(true)
    setError(null)
    try {
      await editItem({
        product_reference_id: productReferenceId,
        location,
        ...(nameChanged ? { name: name.trim() } : {}),
        ...(qtyChanged ? { qty } : {}),
      })
      onClose()
    } catch {
      setError('Failed to save changes. Please try again.')
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />

      <div className="relative w-full max-w-lg bg-surface rounded-t-3xl px-6 pt-5 pb-8 flex flex-col gap-5">
        <div className="w-10 h-1 rounded-full bg-edge mx-auto" />

        <button onClick={onClose} className="absolute top-5 right-5 text-muted hover:text-foreground">
          <X size={20} />
        </button>

        <div>
          <h2 className="font-display text-lg font-semibold text-foreground">Edit Item</h2>
          <p className="text-sm text-muted mt-0.5">Name changes apply across all locations</p>
        </div>

        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-muted">Name</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full bg-raised rounded-xl px-4 py-3 text-foreground text-sm outline-none focus:ring-2 focus:ring-accent"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-muted">Quantity ({unitLabel(unit)})</label>
            <input
              type="number"
              inputMode="decimal"
              min="0.1"
              value={qtyStr}
              onChange={e => setQtyStr(e.target.value)}
              className="w-full bg-raised rounded-xl px-4 py-3 text-foreground text-sm outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
        </div>

        {error && (
          <p className="text-sm text-warn px-3 py-2 bg-warn-dim rounded-xl">{error}</p>
        )}

        <button
          onClick={handleSave}
          disabled={!canSave || saving}
          className="w-full py-4 rounded-2xl bg-accent text-white font-semibold text-base flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <Check size={18} />
          {saving ? 'Saving…' : 'Save'}
        </button>
      </div>
    </div>
  )
}
