import { useState } from 'react'
import { Minus, Plus, Check, X } from 'lucide-react'
import { confirmScan } from '../api/items'
import type { ScanLookupOut } from '../interfaces/Inventory'

const LOCATIONS = ['fridge', 'freezer', 'cupboard'] as const
type Location = typeof LOCATIONS[number]

const DEFAULT_LOCATION: Location = 'fridge'

function formatQty(qty: number, unit: string): string {
  if (unit === 'g' && qty >= 1000) return `${(qty / 1000).toFixed(2).replace(/\.?0+$/, '')} kg`
  if (unit === 'ml' && qty >= 1000) return `${(qty / 1000).toFixed(2).replace(/\.?0+$/, '')} L`
  return `${qty % 1 === 0 ? qty : qty.toFixed(1)} ${unit}`
}

interface Props {
  scanResult: ScanLookupOut
  barcode: string
  onClose: () => void
}

export default function ScanConfirmModal({ scanResult, barcode, onClose }: Props) {
  const { product_reference, computed_qty, computed_unit, data_quality_warning } = scanResult
  const [selectedLocation, setSelectedLocation] = useState<Location>(DEFAULT_LOCATION)
  const [multiplier, setMultiplier] = useState(1)
  const [expiryDate, setExpiryDate] = useState('')
  const [confirming, setConfirming] = useState(false)

  const totalQty = computed_qty! * multiplier

  async function handleConfirm() {
    if (confirming) return
    setConfirming(true)
    try {
      await confirmScan(barcode, selectedLocation, multiplier, expiryDate || null)
      onClose()
    } catch {
      setConfirming(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6 flex flex-col gap-5" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h2 className="font-display text-lg font-semibold text-black">Confirm Scan</h2>
          <button onClick={onClose} className="text-muted hover:text-black transition-colors cursor-pointer">
            <X size={20} />
          </button>
        </div>

        <div className="flex items-center gap-4">
          {/* TODO: replace with OpenFoodFacts product image when available
              API: https://world.openfoodfacts.org/api/v0/product/{barcode}.json
              Image field: product.image_front_small_url
              Needs to be stored on ProductReference and returned in ProductReferenceOut */}
          <div className="w-14 h-14 rounded-xl bg-gray-100 flex items-center justify-center shrink-0">
            <span className="text-2xl">📦</span>
          </div>

          <div className="flex-1 min-w-0">
            <h3 className="font-display text-base font-semibold text-black truncate">
              {product_reference.name}
            </h3>
            {product_reference.brands.length > 0 && (
              <p className="text-sm text-muted truncate">
                {product_reference.brands.join(', ')}
              </p>
            )}
            <p className="text-sm text-accent mt-0.5">
              {formatQty(computed_qty!, computed_unit!)} per scan
            </p>
          </div>
        </div>

        {data_quality_warning && (
          <p className="text-sm text-warn px-3 py-2 bg-warn-dim rounded-lg">{data_quality_warning}</p>
        )}

        <div className="flex gap-2">
          {LOCATIONS.map(loc => (
            <button
              key={loc}
              onClick={() => setSelectedLocation(loc)}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                selectedLocation === loc
                  ? 'bg-accent text-white'
                  : 'bg-gray-100 text-muted hover:text-black'
              }`}
            >
              {loc.charAt(0).toUpperCase() + loc.slice(1)}
            </button>
          ))}
        </div>

        <div className="flex flex-col gap-1.5">
          <label className="text-sm font-medium text-muted">Expiry date (optional)</label>
          <input
            type="date"
            value={expiryDate}
            min={new Date().toISOString().slice(0, 10)}
            onChange={e => setExpiryDate(e.target.value)}
            className="w-full border border-edge rounded-lg px-3 py-2 text-sm text-black focus:outline-none focus:ring-2 focus:ring-accent"
          />
        </div>

        <div className="flex items-center justify-between bg-gray-100 rounded-xl px-5 py-4">
          <button
            onClick={() => setMultiplier(m => Math.max(1, m - 1))}
            disabled={multiplier === 1}
            className="w-10 h-10 rounded-full border border-edge bg-white flex items-center justify-center text-black disabled:text-subtle disabled:border-subtle cursor-pointer disabled:cursor-not-allowed"
          >
            <Minus size={16} />
          </button>

          <div className="text-center">
            <span className="text-4xl font-bold text-black">×{multiplier}</span>
            <p className="text-sm text-muted mt-1">
              Total: <span className="text-black font-medium">{formatQty(totalQty, computed_unit!)}</span>
            </p>
          </div>

          <button
            onClick={() => setMultiplier(m => m + 1)}
            className="w-10 h-10 rounded-full border border-edge bg-white flex items-center justify-center text-black cursor-pointer"
          >
            <Plus size={16} />
          </button>
        </div>

        <button
          onClick={handleConfirm}
          disabled={confirming}
          className="w-full py-2.5 rounded-lg text-sm font-semibold bg-accent hover:bg-accent-hover text-white transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          <Check size={16} />
          {confirming ? 'Adding…' : 'Confirm'}
        </button>
      </div>
    </div>
  )
}
