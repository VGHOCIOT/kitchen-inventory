import { useState } from 'react'
import { useSelector } from 'react-redux'
import { RootState } from '../store'
import { ScanBarcode } from 'lucide-react'
import { useScanContext } from '../App'
import EditItemModal from '../components/EditItemModal'
import LotDetailsModal from '../components/LotDetailsModal'
import type { ItemWithProduct } from '../interfaces/Inventory'
import { computeExpiryStatus } from '../interfaces/Inventory'
import { deleteItem } from '../api/items'

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
  const [lotsOpen, setLotsOpen] = useState<ItemWithProduct | null>(null)
  const { openManual } = useScanContext()

  async function handleDelete(productReferenceId: string, location: string) {
    await deleteItem(productReferenceId, location)
  }

  const locationItems = items.filter(({ item }) => item.location === activeLocation)

  const activeLocations = LOCATIONS.filter(loc => items.some(({ item }) => item.location === loc))
  const locationList = activeLocations.length === 0
    ? 'no locations'
    : activeLocations.length === 1
    ? activeLocations[0]
    : activeLocations.slice(0, -1).join(', ') + ' & ' + activeLocations[activeLocations.length - 1]

  return (
    <div className="flex flex-col h-full bg-white">
      <div className="px-8 pt-8 pb-2 shrink-0">
        <h1 className="font-display text-4xl font-bold text-black leading-tight">What's in stock</h1>
        <p className="text-sm text-muted mt-1.5">
          {items.length} {items.length === 1 ? 'item' : 'items'} across {locationList}
        </p>
      </div>

      <div className="flex px-8 mt-5 border-b border-edge shrink-0">
        {LOCATIONS.map(loc => (
          <button
            key={loc}
            onClick={() => setActiveLocation(loc)}
            className={`mr-7 pb-3 text-sm transition-colors ${
              activeLocation === loc
                ? 'font-semibold text-black border-b-[2.5px] border-black -mb-px'
                : 'text-muted'
            }`}
          >
            {loc.charAt(0).toUpperCase() + loc.slice(1)}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto">
        {locationItems.length === 0 && (
          <p className="px-8 py-10 text-muted text-center">
            Nothing in {activeLocation.charAt(0).toUpperCase() + activeLocation.slice(1)}
          </p>
        )}
        {locationItems.map(({ item, product }) => (
          <div
            key={item.id}
            className="group flex items-center px-8 border-b border-dotted border-edge min-h-[3.25rem] overflow-hidden hover:bg-[#f7fbf9] transition-colors"
          >
            <div className="flex-1">
            <span className="text-base text-black">{product.name}</span>
            {(() => {
              const status = computeExpiryStatus(item.expires_at, item.location)
              if (!status) return null
              const cls = status === 'expired'
                ? 'bg-red-100 text-red-700'
                : status === 'nearing'
                ? 'bg-amber-100 text-amber-700'
                : 'bg-green-100 text-green-700'
              const label = status === 'expired' ? 'Expired' : status === 'nearing' ? 'Soon' : 'Good'
              return <span className={`ml-2 text-xs font-medium px-2 py-0.5 rounded-full ${cls}`}>{label}</span>
            })()}
            </div>
            <div className="flex items-center gap-3 shrink-0">
              <button
                onClick={() => setLotsOpen({ item, product })}
                className="border border-edge text-muted text-sm px-3 py-1 rounded focus:outline-none opacity-0 translate-x-3 pointer-events-none transition-all duration-300 ease-in-out group-hover:opacity-100 group-hover:translate-x-0 group-hover:pointer-events-auto hover:border-black hover:text-black"
              >
                lots
              </button>
              <button
                onClick={() => setEditing({ item, product })}
                className="border border-edge text-muted text-sm px-3 py-1 rounded focus:outline-none opacity-0 translate-x-3 pointer-events-none transition-all duration-300 ease-in-out group-hover:opacity-100 group-hover:translate-x-0 group-hover:pointer-events-auto hover:border-black hover:text-black"
              >
                edit
              </button>
              <button
                onClick={() => handleDelete(item.product_reference_id, item.location)}
                className="border border-danger text-danger text-sm px-3 py-1 rounded focus:outline-none opacity-0 translate-x-3 pointer-events-none transition-all duration-300 ease-in-out group-hover:opacity-100 group-hover:translate-x-0 group-hover:pointer-events-auto hover:bg-red-50"
              >
                remove
              </button>
              <span className="text-sm font-medium text-accent min-w-[4rem] text-right">
                {formatQty(item.qty, item.unit)}
              </span>
            </div>
          </div>
        ))}
      </div>

      <button
        className="fixed bottom-6 right-6 z-50 text-white bg-accent box-border border border-transparent hover:bg-accent-hover shadow-sm font-medium leading-5 rounded-full text-sm p-5 focus:outline-none"
        onClick={openManual}
      >
        <ScanBarcode size={25} />
      </button>

      {editing && (
        <EditItemModal
          itemId={editing.item.id}
          currentLocation={editing.item.location}
          currentName={editing.product.name}
          currentQty={editing.item.qty}
          unit={editing.item.unit}
          onClose={() => setEditing(null)}
          onSaved={() => setEditing(null)}
        />
      )}

      {lotsOpen && (
        <LotDetailsModal
          productReferenceId={lotsOpen.item.product_reference_id}
          location={lotsOpen.item.location}
          productName={lotsOpen.product.name}
          onClose={() => setLotsOpen(null)}
        />
      )}
    </div>
  )
}
