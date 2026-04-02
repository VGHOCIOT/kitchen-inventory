import type { RecipeMatchResponse, RecipeResponse, CookResponse } from '../interfaces/Recipes'

export async function fetchMatchedRecipes(): Promise<RecipeMatchResponse> {
  const res = await fetch('/api/v1/recipes/match-inventory')
  if (!res.ok) throw new Error(`Failed to fetch recipes: ${res.status}`)
  return res.json()
}

export async function fetchRecipeInstructions(recipeId: string): Promise<RecipeResponse> {
  const res = await fetch(`/api/v1/recipes/${recipeId}`)
  if (!res.ok) throw new Error(`Failed to fetch recipe instructions: ${res.status}`)
  return res.json()
}

export async function cookRecipe(recipeId: string, substitutions?: Record<string, string>): Promise<CookResponse> {
  const res = await fetch('/api/v1/items/cook', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recipe_id: recipeId, substitutions }),
  })
  if (!res.ok) throw new Error(`Failed to cook recipe: ${res.status}`)
  return res.json()
}
