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
  item: ItemOut
  data_quality_warning: string | null
}
