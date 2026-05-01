// Each item has shape: { item: ItemOut, product: ProductReferenceOut }
// ItemOut:           { id, product_reference_id, location, qty, unit, expires_at }
// ProductReferenceOut: { id, name, brands, categories, package_quantity, package_unit, ... }

import { ItemWithProduct, ScanOut, ScanIn } from "../interfaces/Inventory"

export interface AddFreshIn {
  name: string
  weight_grams: number
  location: string
  categories?: string[]
  brands?: string[]
}

export async function fetchItems(): Promise<ItemWithProduct[]> {
  const res = await fetch('/api/v1/items/')
  if (!res.ok) throw new Error(`Failed to fetch items: ${res.status}`)
  return res.json()
}

export async function scanBarcode(scan: ScanIn): Promise<ScanOut> {
  const res = await fetch('/api/v1/items/scan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(scan),
  })
  if (!res.ok) throw new Error(`Scan failed: ${res.status}`)
  return res.json()
}

export async function addFreshItem(payload: AddFreshIn): Promise<ScanOut> {
  const res = await fetch('/api/v1/items/add-fresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Add fresh failed: ${res.status}`)
  return res.json()
}

export async function adjustQuantity(
  productReferenceId: string,
  location: string,
  delta: number,
): Promise<void> {
  const res = await fetch('/api/v1/items/adjust', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_reference_id: productReferenceId, location, delta }),
  })
  if (!res.ok) throw new Error(`Adjust failed: ${res.status}`)
}

export interface EditItemIn {
  product_reference_id: string
  location: string
  qty?: number
  name?: string
}

export async function editItem(payload: EditItemIn): Promise<void> {
  const res = await fetch('/api/v1/items/edit', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Edit failed: ${res.status}`)
}

export async function moveItem(
  productReferenceId: string,
  fromLocation: string,
  toLocation: string,
  quantity: number,
): Promise<void> {
  const res = await fetch('/api/v1/items/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      product_reference_id: productReferenceId,
      from_location: fromLocation,
      to_location: toLocation,
      quantity,
    }),
  })
  if (!res.ok) throw new Error(`Move failed: ${res.status}`)
}

