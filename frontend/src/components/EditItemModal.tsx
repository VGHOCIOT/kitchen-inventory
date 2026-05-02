import { useState } from 'react'
import { Check, X } from 'lucide-react'
import { editItem } from '../api/items'

const LOCATIONS = ['fridge', 'freezer', 'cupboard'] as const
type Location = typeof LOCATIONS[number]

function unitLabel(unit: string): string {
  if (unit === 'g') return 'grams'
  if (unit === 'ml') return 'ml'
  return 'count'
}

interface Props {
  itemId: string
  currentLocation: string
  currentName: string
  currentQty: number
  unit: string
  onClose: () => void
  onSaved: () => void
}

export default function EditItemModal({ itemId, currentLocation, currentName, currentQty, unit, onClose, onSaved }: Props) {
  const [name, setName] = useState(currentName)
  const [qtyStr, setQtyStr] = useState(String(currentQty % 1 === 0 ? currentQty : currentQty.toFixed(1)))
  const [location, setLocation] = useState<Location>(currentLocation as Location)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const qty = parseFloat(qtyStr)
  const nameChanged = name.trim() !== currentName
  const qtyChanged = !isNaN(qty) && qty > 0 && qty !== currentQty
  const locationChanged = location !== currentLocation
  const canSave = (nameChanged || qtyChanged || locationChanged) && name.trim().length > 0 && !isNaN(qty) && qty > 0

  async function handleSave() {
    if (!canSave || saving) return
    setSaving(true)
    setError(null)
    try {
      await editItem({
        item_id: itemId,
        ...(nameChanged ? { name: name.trim() } : {}),
        ...(qtyChanged ? { qty } : {}),
        ...(locationChanged ? { location } : {}),
      })
      onSaved()
      onClose()
    } catch {
      setError('Failed to save changes. Please try again.')
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6 flex flex-col gap-5" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-display text-lg font-semibold text-black">Edit Item</h2>
            <p className="text-sm text-muted mt-0.5">Name changes apply across all locations</p>
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
            <label className="text-sm font-medium text-muted">Quantity ({unitLabel(unit)})</label>
            <input
              type="number"
              inputMode="decimal"
              min="0.1"
              value={qtyStr}
              onChange={e => setQtyStr(e.target.value)}
              className="w-full border border-edge rounded-lg px-3 py-2 text-sm text-black focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-sm font-medium text-muted">Location</label>
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
          </div>
        </div>

        {error && <p className="text-sm text-red-500">{error}</p>}

        <button
          onClick={handleSave}
          disabled={!canSave || saving}
          className="w-full py-2.5 rounded-lg text-sm font-semibold bg-accent hover:bg-accent-hover text-white transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <Check size={16} />
          {saving ? 'Saving…' : 'Save'}
        </button>
      </div>
    </div>
  )
}
