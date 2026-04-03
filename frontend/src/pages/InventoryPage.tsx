import { useState } from 'react'
import { useSelector } from 'react-redux'
import { RootState } from '../store'

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
            <span className="text-muted text-sm shrink-0 ml-3">
              {formatQty(item.qty, item.unit)}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
