import { type ReactElement, useEffect } from 'react';
import {
  createBrowserRouter,
  RouterProvider,
  type RouteObject
} from 'react-router-dom'
import { useDispatch } from 'react-redux'
import { AppDispatch } from './store'
import InventoryPage from './pages/InventoryPage'
import CookableRecipes from './pages/CookableRecipes'
import RecipeInstructions from './pages/RecipeInstructions'
import Paths from './interfaces/Pages'
import RecipeActions from './store/actions/recipeActions'
import InventoryActions from './store/actions/inventoryActions'

const routes: RouteObject[] = [
  {
    path: Paths.inventory.path,
    element: <InventoryPage />
  },
  {
    path: Paths.cookableRecipes.path,
    element: <CookableRecipes />
  },
  {
    path: Paths.recipeInstructions.path,
    element: <RecipeInstructions />
  }
];

const router = createBrowserRouter(routes)

function AppWithStore(): ReactElement {
  const dispatch = useDispatch<AppDispatch>()

  useEffect(() => {
    dispatch(InventoryActions.fetchInventory())
    dispatch(RecipeActions.fetchRecipeMatches())

    const ws = new WebSocket(`ws://${window.location.host}/ws`)

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg.event === 'item_added' || msg.event === 'item_deleted' || msg.event === 'recipe_added' || msg.event === 'recipe_deleted' ) {
        dispatch(InventoryActions.fetchInventory())
        dispatch(RecipeActions.fetchRecipeMatches())
      }
    }

    return () => ws.close()
  }, [dispatch])

  return <RouterProvider router={router} />
}

export default (): ReactElement => (
  <AppWithStore />
)
