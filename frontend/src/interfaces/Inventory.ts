export interface ItemOut {
  id: string
  product_reference_id: string
  location: string
  qty: number
  unit: string
  expires_at: string | null
}

export interface ProductReferenceOut {
  id: string
  name: string
  brands: string[]
  categories: string[]
  package_quantity: number | null
  package_unit: string | null
}

export interface ItemWithProduct {
  item: ItemOut
  product: ProductReferenceOut
}

export interface ScanLookupOut {
  product_reference: ProductReferenceOut
  computed_qty: number | null
  computed_unit: string | null
  data_quality_warning: string | null
  requires_manual_entry: boolean
}

export interface ScanOut {
  product_reference: ProductReferenceOut
  item: ItemOut | null
  data_quality_warning: string | null
  requires_manual_entry: boolean
}

export interface StockLotOut {
  id: string
  product_reference_id: string
  location: string
  initial_quantity: number
  remaining_quantity: number
  unit: string
  expires_at: string | null
  opened_at: string | null
  created_at: string
}

export type ExpiryStatus = 'good' | 'nearing' | 'expired'

const NEARING_THRESHOLDS: Record<string, number> = {
  fridge: 3,
  freezer: 30,
  cupboard: 7,
}

export function computeExpiryStatus(expiresAt: string | null, location: string): ExpiryStatus | null {
  if (!expiresAt) return null
  const days = Math.floor((new Date(expiresAt).getTime() - Date.now()) / 86400000)
  const threshold = NEARING_THRESHOLDS[location] ?? 7
  if (days < 0) return 'expired'
  if (days <= threshold) return 'nearing'
  return 'good'
}

