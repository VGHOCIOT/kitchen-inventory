import { useState } from 'react'
import { Check, X } from 'lucide-react'
import { addFreshItem } from '../api/items'
import type { ScanOut } from '../interfaces/Inventory'

const LOCATIONS = ['fridge', 'freezer', 'cupboard'] as const
type Location = typeof LOCATIONS[number]

interface Props {
  scanResult: ScanOut
  onClose: () => void
}

export default function ManualEntryModal({ scanResult, onClose }: Props) {
  const { product_reference } = scanResult
  const [name, setName] = useState(product_reference.name)
  const [weightStr, setWeightStr] = useState('')
  const [location, setLocation] = useState<Location>('fridge')
  const [confirming, setConfirming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const weight = parseFloat(weightStr)
  const canConfirm = name.trim().length > 0 && !isNaN(weight) && weight > 0

  async function handleConfirm() {
    if (!canConfirm || confirming) return
    setConfirming(true)
    setError(null)
    try {
      await addFreshItem({
        name: name.trim(),
        weight_grams: weight,
        location,
        categories: product_reference.categories ?? undefined,
        brands: product_reference.brands ?? undefined,
      })
      onClose()
    } catch {
      setError('Failed to add item. Please try again.')
      setConfirming(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />

      <div className="relative w-full max-w-lg bg-surface rounded-t-3xl px-6 pt-5 pb-8 flex flex-col gap-5">
        <div className="w-10 h-1 rounded-full bg-edge mx-auto" />

        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-muted hover:text-foreground"
        >
          <X size={20} />
        </button>

        <div>
          <h2 className="font-display text-lg font-semibold text-foreground">Manual Entry</h2>
          <p className="text-sm text-muted mt-0.5">Product data incomplete — enter details below</p>
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
            <label className="text-sm font-medium text-muted">Weight (grams)</label>
            <input
              type="number"
              inputMode="decimal"
              min="1"
              value={weightStr}
              onChange={e => setWeightStr(e.target.value)}
              placeholder="e.g. 500"
              className="w-full bg-raised rounded-xl px-4 py-3 text-foreground text-sm outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
        </div>

        <div className="flex gap-2">
          {LOCATIONS.map(loc => (
            <button
              key={loc}
              onClick={() => setLocation(loc)}
              className={`flex-1 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
                location === loc
                  ? 'bg-accent text-white'
                  : 'bg-raised text-muted'
              }`}
            >
              {loc.charAt(0).toUpperCase() + loc.slice(1)}
            </button>
          ))}
        </div>

        {error && (
          <p className="text-sm text-warn px-3 py-2 bg-warn-dim rounded-xl">{error}</p>
        )}

        <button
          onClick={handleConfirm}
          disabled={!canConfirm || confirming}
          className="w-full py-4 rounded-2xl bg-accent text-white font-semibold text-base flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <Check size={18} />
          {confirming ? 'Adding…' : 'Add Item'}
        </button>
      </div>
    </div>
  )
}
