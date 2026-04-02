export interface Page {
  title: string
  path: string
  navigable?: boolean
}

export type Pages = Record<string, Page>

const pages = {
  inventory: {
    title: 'Inventory',
    path: '/inventory',
    navigable: true,
  },
  cookableRecipes: {
    title: 'Cookable Recipes',
    path: '/cookable-recipes',
    navigable: true,
  },
  recipeInstructions: {
    title: 'Recipe Instructions',
    path: '/recipes/:id',
    navigable: false,
  },
} satisfies Pages

export default pages
