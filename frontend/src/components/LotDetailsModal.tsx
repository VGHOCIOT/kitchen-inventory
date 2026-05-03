import { useEffect, useState } from 'react'
import { X, PackageOpen } from 'lucide-react'
import { getLots, updateLot } from '../api/items'
import type { StockLotOut } from '../interfaces/Inventory'
import { suggestExpiryAfterOpening } from '../interfaces/Inventory'

interface Props {
  productReferenceId: string
  location: string
  productName: string
  categories: string[]
  onClose: () => void
}

function formatQty(qty: number, unit: string): string {
  if (unit === 'g' && qty >= 1000) return `${(qty / 1000).toFixed(2).replace(/\.?0+$/, '')} kg`
  if (unit === 'ml' && qty >= 1000) return `${(qty / 1000).toFixed(2).replace(/\.?0+$/, '')} L`
  return `${qty % 1 === 0 ? qty : qty.toFixed(1)} ${unit}`
}

function toDateInputValue(iso: string | null): string {
  if (!iso) return ''
  return iso.slice(0, 10)
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function LotDetailsModal({ productReferenceId, location, productName, categories, onClose }: Props) {
  const [lots, setLots] = useState<StockLotOut[]>([])
  const [loading, setLoading] = useState(true)
  const [openingLotId, setOpeningLotId] = useState<string | null>(null)
  const [openingExpiry, setOpeningExpiry] = useState<Record<string, string>>({})

  async function refresh() {
    setLoading(true)
    try {
      const data = await getLots(productReferenceId, location)
      setLots(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { refresh() }, [productReferenceId, location])

  async function handleExpiryBlur(lotId: string, value: string) {
    const expires_at = value ? new Date(value).toISOString() : null
    await updateLot(lotId, { expires_at })
    await refresh()
  }

  function startOpening(lot: StockLotOut) {
    const suggested = suggestExpiryAfterOpening(categories, location)
    setOpeningExpiry(prev => ({ ...prev, [lot.id]: suggested.toISOString().slice(0, 10) }))
    setOpeningLotId(lot.id)
  }

  async function confirmOpening(lotId: string) {
    const expiryVal = openingExpiry[lotId]
    await updateLot(lotId, {
      opened_at: new Date().toISOString(),
      expires_at: expiryVal ? new Date(expiryVal).toISOString() : null,
    })
    setOpeningLotId(null)
    await refresh()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div
        className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6 flex flex-col gap-4 max-h-[85vh] overflow-y-auto"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-display text-lg font-semibold text-black">Lots</h2>
            <p className="text-sm text-muted">{productName} · {location}</p>
          </div>
          <button onClick={onClose} className="text-muted hover:text-black transition-colors cursor-pointer">
            <X size={20} />
          </button>
        </div>

        {loading && <p className="text-sm text-muted text-center py-4">Loading…</p>}

        {!loading && lots.length === 0 && (
          <p className="text-sm text-muted text-center py-4">No active lots.</p>
        )}

        {!loading && lots.map(lot => (
          <div key={lot.id} className="border border-edge rounded-xl p-4 flex flex-col gap-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-black">
                {formatQty(lot.remaining_quantity, lot.unit)} remaining
              </span>
              <span className="text-xs text-muted">Added {formatDate(lot.created_at)}</span>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs text-muted font-medium">Expiry date</label>
              <input
                type="date"
                defaultValue={toDateInputValue(lot.expires_at)}
                onBlur={e => handleExpiryBlur(lot.id, e.target.value)}
                className="border border-edge rounded-lg px-3 py-1.5 text-sm text-black focus:outline-none focus:ring-2 focus:ring-accent"
              />
            </div>

            {lot.opened_at ? (
              <p className="text-xs text-muted">
                Opened {formatDate(lot.opened_at)}
              </p>
            ) : openingLotId === lot.id ? (
              <div className="flex flex-col gap-2">
                <label className="text-xs text-muted font-medium">New expiry after opening</label>
                <input
                  type="date"
                  value={openingExpiry[lot.id] ?? ''}
                  onChange={e => setOpeningExpiry(prev => ({ ...prev, [lot.id]: e.target.value }))}
                  className="border border-edge rounded-lg px-3 py-1.5 text-sm text-black focus:outline-none focus:ring-2 focus:ring-accent"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => confirmOpening(lot.id)}
                    className="flex-1 py-1.5 rounded-lg text-sm font-medium bg-accent text-white hover:bg-accent-hover transition-colors cursor-pointer"
                  >
                    Confirm opened
                  </button>
                  <button
                    onClick={() => setOpeningLotId(null)}
                    className="px-4 py-1.5 rounded-lg text-sm font-medium border border-edge text-muted hover:text-black transition-colors cursor-pointer"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <button
                onClick={() => startOpening(lot)}
                className="flex items-center gap-1.5 self-start text-sm text-muted hover:text-black transition-colors cursor-pointer"
              >
                <PackageOpen size={14} />
                Mark opened
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
