import { useState } from 'react'
import { Check, X } from 'lucide-react'
import { addFreshItem } from '../api/items'

const LOCATIONS = ['fridge', 'freezer', 'cupboard'] as const
type Location = typeof LOCATIONS[number]

interface Props {
  initialName?: string
  initialCategories?: string[]
  initialBrands?: string[]
  onClose: () => void
}

export default function ManualEntryModal({ initialName, initialCategories, initialBrands, onClose }: Props) {
  const [name, setName] = useState(initialName || '')
  const [categories] = useState(initialCategories || [])
  const [brands] = useState(initialBrands || [])
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
        categories: categories.length > 0 ? categories : undefined,
        brands: brands.length > 0 ? brands : undefined,
      })
      onClose()
    } catch {
      setError('Failed to add item. Please try again.')
      setConfirming(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6 flex flex-col gap-5" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-display text-lg font-semibold text-black">Manual Entry</h2>
            <p className="text-sm text-muted mt-0.5">Product data incomplete — enter details below</p>
          </div>
          <button onClick={onClose} className="text-muted hover:text-black transition-colors cursor-pointer">
            <X size={20} />
          </button>
        </div>

        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-muted">Name</label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              className="w-full border border-edge rounded-lg px-3 py-2 text-sm text-black focus:outline-none focus:ring-2 focus:ring-accent"
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
              className="w-full border border-edge rounded-lg px-3 py-2 text-sm text-black placeholder:text-subtle focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
        </div>

        <div className="flex gap-2">
          {LOCATIONS.map(loc => (
            <button
              key={loc}
              onClick={() => setLocation(loc)}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                location === loc
                  ? 'bg-accent text-white'
                  : 'bg-gray-100 text-muted hover:text-black'
              }`}
            >
              {loc.charAt(0).toUpperCase() + loc.slice(1)}
            </button>
          ))}
        </div>

        {error && <p className="text-sm text-red-500">{error}</p>}

        <button
          onClick={handleConfirm}
          disabled={!canConfirm || confirming}
          className="w-full py-2.5 rounded-lg text-sm font-semibold bg-accent hover:bg-accent-hover text-white transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <Check size={16} />
          {confirming ? 'Adding…' : 'Add Item'}
        </button>
      </div>
    </div>
  )
}
