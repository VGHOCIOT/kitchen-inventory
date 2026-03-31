import type { RecipeMatchResponse } from '../interfaces/Recipes'

export async function fetchMatchedRecipes(): Promise<RecipeMatchResponse> {
  const res = await fetch('/api/v1/recipes/match-inventory')
  if (!res.ok) throw new Error(`Failed to fetch recipes: ${res.status}`)
  return res.json()
}
