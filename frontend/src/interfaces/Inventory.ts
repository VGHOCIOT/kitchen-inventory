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

export interface ScanOut {
  product_reference: ProductReferenceOut
  item: ItemOut | null
  data_quality_warning: string | null
  requires_manual_entry: boolean
}

export interface ScanIn {
  barcode: string
  location: string
  quantity: number | null
}