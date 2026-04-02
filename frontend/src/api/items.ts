// Each item has shape: { item: ItemOut, product: ProductReferenceOut }
// ItemOut:           { id, product_reference_id, location, qty, unit, expires_at }
// ProductReferenceOut: { id, name, brands, categories, package_quantity, package_unit, ... }

import { ItemWithProduct } from "../interfaces/Inventory"

export async function fetchItems(): Promise<ItemWithProduct[]> {
  const res = await fetch('/api/v1/items/')
  if (!res.ok) throw new Error(`Failed to fetch items: ${res.status}`)
  return res.json()
}

