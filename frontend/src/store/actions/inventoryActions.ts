import { type Dispatch } from '@reduxjs/toolkit'
import { fetchItems } from '../../api/items'
import { actions } from '../slices/inventorySlice'

export default class InventoryActions {
  static fetchInventory = () => async (dispatch: Dispatch) => {
    const data = await fetchItems()
    dispatch(actions.setInventory(data))
  }
}
