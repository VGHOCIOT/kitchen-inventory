// Each item has shape: { item: ItemOut, product: ProductReferenceOut }
// ItemOut:           { id, product_reference_id, location, qty, unit, expires_at }
// ProductReferenceOut: { id, name, brands, categories, package_quantity, package_unit, ... }

export async function fetchItems() {
  const res = await fetch('/api/v1/items/')
  if (!res.ok) throw new Error(`Failed to fetch items: ${res.status}`)
  return res.json()
}

export async function adjustItem({ product_reference_id, location, delta }) {
  const res = await fetch('/api/v1/items/adjust', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_reference_id, location, delta }),
  })
  if (!res.ok) throw new Error(`Failed to adjust item: ${res.status}`)
  return res.json()
}

export async function deleteItem({ product_reference_id, location }) {
  const res = await fetch('/api/v1/items/', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_reference_id, location }),
  })
  if (!res.ok) throw new Error(`Failed to delete item: ${res.status}`)
}

export async function addFreshItem({ name, weight_grams, location = 'fridge' }) {
  const res = await fetch(`/api/v1/items/add-fresh?location=${location}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, weight_grams }),
  })
  if (!res.ok) throw new Error(`Failed to add item: ${res.status}`)
  return res.json()
}
