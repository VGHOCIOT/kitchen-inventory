import { createSlice } from '@reduxjs/toolkit'
import { ItemWithProduct } from '../../interfaces/Inventory'
import * as reducers from '../reducers/inventoryReducers'

const initialState: ItemWithProduct[] = []

const slice = createSlice({
  name: 'inventory',
  initialState,
  reducers,
})

export default slice.reducer
export const actions = slice.actions
