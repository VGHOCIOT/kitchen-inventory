import { useState, useEffect } from 'react'
import { Lock } from 'lucide-react'
import { fetchMatchedRecipes } from '../api/recipes'
import type { RecipeMatchResponse, RecipeMatchResult } from '../interfaces/Recipes'

export default function CookableRecipes() {
  const [data, setData] = useState<RecipeMatchResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchMatchedRecipes()
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p>Loading...</p>
  if (error) return <p>{error}</p>
  if (!data) return null

  // TODO: render recipe cards grouped by unlock state
  // two cards per row, with image, title, description, and lock overlay if not 100% available
  // unlocked recipes have hyperlinks to the cook page (not implemented yet)
  // title of this page should align with the title in the navigation bar ("Cookable Recipes")
  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Cookable Recipes</h1>
      <div>
        <h2 className="text-xl font-semibold mb-2">Unlocked Recipes</h2>
        <div className="flex flex-wrap">
          {data.unlocked.map(recipe => (
            <RecipeCard key={recipe.recipe_id} recipe={recipe} />
          ))}
        </div>

        <h2 className="text-xl font-semibold mt-6 mb-2">Almost Unlocked Recipes</h2>
        <div className="flex flex-wrap">
          {data.almost.map(recipe => (
            <RecipeCard key={recipe.recipe_id} recipe={recipe} />
          ))}
        </div>

        <h2 className="text-xl font-semibold mt-6 mb-2">Locked Recipes</h2>
        <div className="flex flex-wrap">
          {data.locked.map(recipe => (
            <RecipeCard key={recipe.recipe_id} recipe={recipe} />
          ))}
        </div>
      </div>
    </div>
  )
}

// Skeleton for a single recipe card — you'll flesh this out
export function RecipeCard({ recipe: _recipe }: { recipe: RecipeMatchResult }) {
  // _recipe.match_type            — 'unlocked' | 'almost' | 'locked'
  // _recipe.availability_percent  — 0-100, substitutions count as covered
  // _recipe.recipe_image_url      — card artwork (silhouette when locked)
  // _recipe.recipe_description    — teaser text
  // _recipe.missing_ingredients   — hint text on locked/almost cards (no inventory, no sub)
  // _recipe.suggested_substitutions — swap hints for almost cards
  return (
    <div className={`relative w-[300px] border border-gray-300 rounded-lg p-4 m-2 cursor-${_recipe.match_type === 'locked' ? 'not-allowed' : 'pointer'}`}>
        <div>
            <img src={_recipe.recipe_image_url || 'placeholder.jpg'} alt={_recipe.recipe_title} className={`recipe-image ${_recipe.match_type}`} />
            <h3>{_recipe.recipe_title}</h3>
            <p>{_recipe.recipe_description}</p>
            <button disabled={_recipe.match_type !== 'unlocked'}>Cook</button>
        </div>

        {_recipe.match_type === 'locked' && (
            <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center text-white text-lg font-bold">
                <div className="bg-white p-3 rounded-full shadow-lg">
                    <Lock size={24} className="text-slate-500" />
                </div>
            </div>
        )}
    </div>
  )
}
