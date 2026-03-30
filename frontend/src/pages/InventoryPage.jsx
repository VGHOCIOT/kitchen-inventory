import { useState, useEffect } from 'react'
import { fetchItems } from '../api/items'

const LOCATIONS = ['fridge', 'freezer', 'cupboard']

function formatQty(qty, unit) {
  if (unit === 'g' && qty >= 1000) return `${(qty / 1000).toFixed(2).replace(/\.?0+$/, '')} kg`
  if (unit === 'ml' && qty >= 1000) return `${(qty / 1000).toFixed(2).replace(/\.?0+$/, '')} L`
  return `${qty % 1 === 0 ? qty : qty.toFixed(1)} ${unit}`
}

export default function InventoryPage() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeLocation, setActiveLocation] = useState('fridge')

  useEffect(() => {
    fetchItems()
      .then(setItems)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  const locationItems = items.filter(({ item }) => item.location === activeLocation)

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100dvh' }}>

      {/* Location tabs */}
      <div style={{ display: 'flex', borderBottom: '1px solid var(--border)' }}>
        {LOCATIONS.map(loc => (
          <button
            key={loc}
            onClick={() => setActiveLocation(loc)}
            style={{
              flex: 1,
              padding: '16px',
              fontSize: '0.9rem',
              fontWeight: 600,
              letterSpacing: '0.05em',
              color: activeLocation === loc ? 'var(--accent)' : 'var(--text-muted)',
              borderBottom: activeLocation === loc ? '2px solid var(--accent)' : '2px solid transparent',
              background: 'var(--bg)',
            }}
          >
            {loc.charAt(0).toUpperCase() + loc.slice(1)}
          </button>
        ))}
      </div>

      {/* List */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 0' }}>
        {loading && (
          <p style={{ padding: '24px', color: 'var(--text-muted)', textAlign: 'center' }}>
            Loading...
          </p>
        )}
        {error && (
          <p style={{ padding: '24px', color: 'var(--danger)', textAlign: 'center' }}>
            {error}
          </p>
        )}
        {!loading && !error && locationItems.length === 0 && (
          <p style={{ padding: '24px', color: 'var(--text-muted)', textAlign: 'center' }}>
            Nothing in {activeLocation.charAt(0).toUpperCase() + activeLocation.slice(1)}
          </p>
        )}
        {locationItems.map(({ item, product }) => (
          <div
            key={item.id}
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '14px 20px',
              borderBottom: '1px solid var(--border)',
              minHeight: '56px',
            }}
          >
            <span style={{ fontSize: '1rem' }}>{product.name}</span>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.9rem', flexShrink: 0, marginLeft: '12px' }}>
              {formatQty(item.qty, item.unit)}
            </span>
          </div>
        ))}
      </div>

    </div>
  )
}
