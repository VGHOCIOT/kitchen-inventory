import { useState } from 'react'
import { useSelector } from 'react-redux'
import { RootState } from '../store'
import { ScanBarcode } from 'lucide-react'
import { useScanContext } from '../App'
import EditItemModal from '../components/EditItemModal'
import type { ItemWithProduct } from '../interfaces/Inventory'

const LOCATIONS = ['fridge', 'freezer', 'cupboard'] as const
type Location = typeof LOCATIONS[number]

function formatQty(qty: number, unit: string): string {
  if (unit === 'g' && qty >= 1000) return `${(qty / 1000).toFixed(2).replace(/\.?0+$/, '')} kg`
  if (unit === 'ml' && qty >= 1000) return `${(qty / 1000).toFixed(2).replace(/\.?0+$/, '')} L`
  return `${qty % 1 === 0 ? qty : qty.toFixed(1)} ${unit}`
}

export default function InventoryPage() {
  const items = useSelector((state: RootState) => state.inventory)
  const [activeLocation, setActiveLocation] = useState<Location>('fridge')
  const [editing, setEditing] = useState<ItemWithProduct | null>(null)
  const { openManual } = useScanContext()
  const locationItems = items.filter(({ item }) => item.location === activeLocation)

  return (
    <div className="flex flex-col h-dvh bg-white">
      <div className="flex border-b border-edge">
        {LOCATIONS.map(loc => (
          <button
            key={loc}
            onClick={() => setActiveLocation(loc)}
            className={`flex-1 py-4 text-sm font-semibold tracking-wide ${
              activeLocation === loc
                ? 'text-accent border-b-2 border-accent'
                : 'text-muted border-b-2 border-transparent'
            }`}
          >
            {loc.charAt(0).toUpperCase() + loc.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        {locationItems.length === 0 && (
          <p className="p-6 text-muted text-center">
            Nothing in {activeLocation.charAt(0).toUpperCase() + activeLocation.slice(1)}
          </p>
        )}
        {locationItems.map(({ item, product }) => (
          <div
            key={item.id}
            className="flex justify-between items-center px-5 py-3.5 border-b border-edge min-h-14"
          >
            <span className="text-base text-black">{product.name}</span>
            <div className="flex items-center gap-3 shrink-0 ml-3">
              <span className="text-muted text-sm">{formatQty(item.qty, item.unit)}</span>
              <button
                onClick={() => setEditing({ item, product })}
                className="text-xs text-accent font-medium"
              >
                Edit
              </button>
            </div>
          </div>
        ))}
      </div>

      <button
        className="fixed bottom-6 right-6 z-50 text-white bg-accent box-border border border-transparent hover:bg-accent-hover shadow-xs font-medium leading-5 rounded-full text-sm p-5 focus:outline-none"
        onClick={openManual}
      >
        <ScanBarcode size={25} />
      </button>

      {editing && (
        <EditItemModal
          productReferenceId={editing.item.product_reference_id}
          location={editing.item.location}
          currentName={editing.product.name}
          currentQty={editing.item.qty}
          unit={editing.item.unit}
          onClose={() => setEditing(null)}
        />
      )}
    </div>
  )
}
