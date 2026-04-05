// Each item has shape: { item: ItemOut, product: ProductReferenceOut }
// ItemOut:           { id, product_reference_id, location, qty, unit, expires_at }
// ProductReferenceOut: { id, name, brands, categories, package_quantity, package_unit, ... }

import { ItemWithProduct, ScanOut } from "../interfaces/Inventory"

export async function fetchItems(): Promise<ItemWithProduct[]> {
  const res = await fetch('/api/v1/items/')
  if (!res.ok) throw new Error(`Failed to fetch items: ${res.status}`)
  return res.json()
}

export async function scanBarcode(barcode: string, location: string): Promise<ScanOut> {
  const res = await fetch('/api/v1/items/scan', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ barcode, location }),
  })
  if (!res.ok) throw new Error(`Scan failed: ${res.status}`)
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

