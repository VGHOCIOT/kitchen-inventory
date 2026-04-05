import { useState } from 'react'
import { Minus, Plus, Check, X } from 'lucide-react'
import { adjustQuantity } from '../api/items'
import type { ScanOut } from '../interfaces/Inventory'

function formatQty(qty: number, unit: string): string {
  if (unit === 'g' && qty >= 1000) return `${(qty / 1000).toFixed(2).replace(/\.?0+$/, '')} kg`
  if (unit === 'ml' && qty >= 1000) return `${(qty / 1000).toFixed(2).replace(/\.?0+$/, '')} L`
  return `${qty % 1 === 0 ? qty : qty.toFixed(1)} ${unit}`
}

interface Props {
  scanResult: ScanOut
  onClose: () => void
}

export default function ScanConfirmModal({ scanResult, onClose }: Props) {
  const [multiplier, setMultiplier] = useState(1)
  const [confirming, setConfirming] = useState(false)

  const { product_reference, item, data_quality_warning } = scanResult
  const lotQty = item.qty
  const totalQty = lotQty * multiplier

  async function handleConfirm() {
    if (confirming) return
    setConfirming(true)
    try {
      // First lot already added by the scan call.
      // Adjust by (multiplier - 1) additional lots.
      if (multiplier > 1) {
        await adjustQuantity(product_reference.id, item.location, lotQty * (multiplier - 1))
      }
      onClose()
    } catch {
      setConfirming(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />

      {/* Sheet */}
      <div className="relative w-full max-w-lg bg-surface rounded-t-3xl px-6 pt-5 pb-8 flex flex-col gap-5">
        {/* Drag handle */}
        <div className="w-10 h-1 rounded-full bg-edge mx-auto" />

        {/* Dismiss */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-muted hover:text-foreground"
        >
          <X size={20} />
        </button>

        {/* Product */}
        <div className="flex items-center gap-4">
          {/* TODO: replace with OpenFoodFacts product image when available
              API: https://world.openfoodfacts.org/api/v0/product/{barcode}.json
              Image field: product.image_front_small_url
              Needs to be stored on ProductReference and returned in ProductReferenceOut */}
          <div className="w-16 h-16 rounded-xl bg-raised flex items-center justify-center shrink-0">
            <span className="text-3xl">📦</span>
          </div>

          <div className="flex-1 min-w-0">
            <h2 className="text-lg font-semibold text-foreground truncate">
              {product_reference.name}
            </h2>
            {product_reference.brands.length > 0 && (
              <p className="text-sm text-muted truncate">
                {product_reference.brands.join(', ')}
              </p>
            )}
            <p className="text-sm text-accent mt-0.5">
              {formatQty(lotQty, item.unit)} per scan
            </p>
          </div>
        </div>

        {data_quality_warning && (
          <p className="text-sm text-warn px-3 py-2 bg-warn-dim rounded-xl">
            {data_quality_warning}
          </p>
        )}

        {/* Multiplier */}
        <div className="flex items-center justify-between bg-raised rounded-2xl px-5 py-4">
          <button
            onClick={() => setMultiplier(m => Math.max(1, m - 1))}
            disabled={multiplier === 1}
            className="w-11 h-11 rounded-full border border-edge flex items-center justify-center text-foreground disabled:text-subtle disabled:border-subtle"
          >
            <Minus size={18} />
          </button>

          <div className="text-center">
            <span className="text-4xl font-bold text-foreground">×{multiplier}</span>
            <p className="text-sm text-muted mt-1">
              Total: <span className="text-foreground font-medium">{formatQty(totalQty, item.unit)}</span>
            </p>
          </div>

          <button
            onClick={() => setMultiplier(m => m + 1)}
            className="w-11 h-11 rounded-full border border-edge flex items-center justify-center text-foreground"
          >
            <Plus size={18} />
          </button>
        </div>

        {/* Confirm */}
        <button
          onClick={handleConfirm}
          disabled={confirming}
          className="w-full py-4 rounded-2xl bg-accent text-white font-semibold text-base flex items-center justify-center gap-2 disabled:opacity-50"
        >
          <Check size={18} />
          {confirming ? 'Adding…' : 'Confirm'}
        </button>
      </div>
    </div>
  )
}
