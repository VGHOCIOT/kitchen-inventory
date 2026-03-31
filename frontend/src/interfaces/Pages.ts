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
    title: 'Recipes',
    path: '/recipes',
    navigable: true,
  },
} satisfies Pages

export default pages
