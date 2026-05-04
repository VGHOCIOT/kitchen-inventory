import { useEffect, useState } from 'react'
import { X, PackageOpen } from 'lucide-react'
import { getLots, updateLot } from '../api/items'
import type { StockLotOut } from '../interfaces/Inventory'

interface Props {
  productReferenceId: string
  location: string
  productName: string
  onClose: () => void
}

function formatQty(qty: number, unit: string): string {
  if (unit === 'g' && qty >= 1000) return `${(qty / 1000).toFixed(2).replace(/\.?0+$/, '')} kg`
  if (unit === 'ml' && qty >= 1000) return `${(qty / 1000).toFixed(2).replace(/\.?0+$/, '')} L`
  return `${qty % 1 === 0 ? qty : qty.toFixed(1)} ${unit}`
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

export default function LotDetailsModal({ productReferenceId, location, productName, onClose }: Props) {
  const [lots, setLots] = useState<StockLotOut[]>([])
  const [loading, setLoading] = useState(true)
  const [openingLotId, setOpeningLotId] = useState<string | null>(null)

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

  async function confirmOpening(lotId: string) {
    await updateLot(lotId, { opened_at: new Date().toISOString() })
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

            {lot.expires_at && (
              <p className="text-xs text-muted">
                Expires {formatDate(lot.expires_at)}
              </p>
            )}

            {lot.opened_at ? (
              <p className="text-xs text-muted">
                Opened {formatDate(lot.opened_at)}
              </p>
            ) : openingLotId === lot.id ? (
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
            ) : (
              <button
                onClick={() => setOpeningLotId(lot.id)}
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
