import type { ReactElement } from 'react';
import {
  createBrowserRouter,
  RouterProvider,
  type RouteObject
} from 'react-router-dom'
import InventoryPage from './pages/InventoryPage'
import CookableRecipes from './pages/CookableRecipes'
import RecipeInstructions from './pages/RecipeInstructions'
import Paths from './interfaces/Pages';


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

export default (): ReactElement => {
  return(
    <>
      <RouterProvider
        router={createBrowserRouter(routes)}
      ></RouterProvider>
    </>
  );
};
