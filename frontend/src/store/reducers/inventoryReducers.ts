import { type PayloadAction } from '@reduxjs/toolkit'
import { ItemWithProduct } from '../../interfaces/Inventory'

export const setInventory = (_state: ItemWithProduct[], action: PayloadAction<ItemWithProduct[]>): ItemWithProduct[] => {
  return action.payload
}
