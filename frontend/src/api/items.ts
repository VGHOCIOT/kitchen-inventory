// Each item has shape: { item: ItemOut, product: ProductReferenceOut }
// ItemOut:           { id, product_reference_id, location, qty, unit, expires_at }
// ProductReferenceOut: { id, name, brands, categories, package_quantity, package_unit, ... }

import { ItemWithProduct, ScanLookupOut, ScanOut, StockLotOut } from "../interfaces/Inventory"

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

export async function scanBarcode(barcode: string): Promise<ScanLookupOut> {
  const res = await fetch('/api/v1/items/scan/lookup', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ barcode }),
  })
  if (!res.ok) throw new Error(`Scan lookup failed: ${res.status}`)
  return res.json()
}

export async function confirmScan(
  barcode: string,
  location: string,
  multiplier: number,
  expiresAt?: string | null,
): Promise<ScanOut> {
  const body: Record<string, unknown> = { barcode, location, multiplier }
  if (expiresAt) body.expires_at = expiresAt
  const res = await fetch('/api/v1/items/scan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Scan confirm failed: ${res.status}`)
  return res.json()
}

export async function getLots(productReferenceId: string, location: string): Promise<StockLotOut[]> {
  const res = await fetch(`/api/v1/items/lots/${productReferenceId}/${location}`)
  if (!res.ok) throw new Error(`Failed to fetch lots: ${res.status}`)
  return res.json()
}

export async function updateLot(
  lotId: string,
  body: { expires_at?: string | null; opened_at?: string | null },
): Promise<StockLotOut> {
  const res = await fetch(`/api/v1/items/lots/${lotId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`Update lot failed: ${res.status}`)
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


export interface EditItemIn {
  item_id: string
  location?: string
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

export async function deleteItem(productReferenceId: string, location: string): Promise<void> {
  const res = await fetch('/api/v1/items/', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_reference_id: productReferenceId, location }),
  })
  if (!res.ok) throw new Error(`Delete failed: ${res.status}`)
}


