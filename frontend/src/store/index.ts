import { configureStore } from '@reduxjs/toolkit'
import recipeReducer from './slices/recipeSlice'
import inventoryReducer from './slices/inventorySlice'

export const store = configureStore({
  reducer: {
    recipes: recipeReducer,
    inventory: inventoryReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
