import type { ReactElement } from 'react';
import {
  createBrowserRouter,
  RouterProvider,
  type RouteObject
} from 'react-router-dom'
import InventoryPage from './pages/InventoryPage'
import CookableRecipes from './pages/CookableRecipes'
import Paths from './interfaces/Pages';


const routes: RouteObject[] = [
  {
    path: Paths.inventory.path,
    element: <InventoryPage />
  },
  {
    path: Paths.cookableRecipes.path,
    element: <CookableRecipes />
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
