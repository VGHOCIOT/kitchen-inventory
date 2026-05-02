import type { RecipeMatchResponse, RecipeResponse, CookResponse, CookPlan, RecipeOut } from '../interfaces/Recipes'

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

export async function fetchCookPlan(recipeId: string): Promise<CookPlan> {
  const res = await fetch(`/api/v1/recipes/${recipeId}/cook-plan`)
  if (!res.ok) throw new Error(`Failed to fetch cook plan: ${res.status}`)
  return res.json()
}

export async function createRecipeFromUrl(url: string): Promise<RecipeOut> {
  const res = await fetch('/api/v1/recipes/from-url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  if (res.status === 409) throw new Error('Recipe already exists')
  if (res.status === 400) throw new Error('Could not parse recipe from that URL')
  if (!res.ok) throw new Error(`Failed to add recipe: ${res.status}`)
  return res.json()
}

export async function cookRecipe(
  recipeId: string,
  substitutions?: Record<string, string>,
  skipped?: string[],
  scale?: number,
): Promise<CookResponse> {
  const res = await fetch('/api/v1/items/cook', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recipe_id: recipeId, substitutions, skipped, scale }),
  })
  if (!res.ok) throw new Error(`Failed to cook recipe: ${res.status}`)
  return res.json()
}
