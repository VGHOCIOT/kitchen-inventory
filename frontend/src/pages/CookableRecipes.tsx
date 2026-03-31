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

  if (loading) return <p className="p-6 text-slate-400">Loading recipes…</p>
  if (error) return <p className="p-6 text-red-400">{error}</p>
  if (!data) return null

  const Section = ({ title, recipes }: { title: string; recipes: RecipeMatchResult[] }) => {
    if (recipes.length === 0) return null
    return (
      <section className="mb-10">
        <h2 className="text-lg font-semibold text-slate-300 mb-4 uppercase tracking-wide">{title}</h2>
        <div className="grid grid-cols-2 gap-4">
          {recipes.map(recipe => (
            <RecipeCard key={recipe.recipe_id} recipe={recipe} />
          ))}
        </div>
      </section>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold text-white mb-8">Cookable Recipes</h1>
      <Section title="Unlocked" recipes={data.unlocked} />
      <Section title="Almost There" recipes={data.almost} />
      <Section title="Locked" recipes={data.locked} />
    </div>
  )
}

export function RecipeCard({ recipe }: { recipe: RecipeMatchResult }) {
  const isLocked = recipe.match_type === 'locked'
  const isAlmost = recipe.match_type === 'almost'

  const badgeClass = isLocked
    ? 'bg-slate-700 text-slate-400'
    : isAlmost
    ? 'bg-amber-900/60 text-amber-300'
    : 'bg-emerald-900/60 text-emerald-300'

  return (
    <div className={`relative rounded-xl overflow-hidden bg-slate-800 border border-slate-700 flex flex-col ${isLocked ? 'opacity-70' : ''}`}>
      {/* Image */}
      <div className="relative h-48 bg-slate-700">
        {recipe.recipe_image_url ? (
          <img
            src={recipe.recipe_image_url}
            alt={recipe.recipe_title}
            className={`w-full h-full object-cover ${isLocked ? 'grayscale' : ''}`}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-slate-500 text-sm">No image</div>
        )}

        {/* Lock overlay */}
        {isLocked && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
            <div className="bg-slate-900/80 p-3 rounded-full">
              <Lock size={28} className="text-slate-400" />
            </div>
          </div>
        )}

        {/* Availability badge */}
        <span className={`absolute top-2 right-2 text-xs font-semibold px-2 py-1 rounded-full ${badgeClass}`}>
          {recipe.availability_percent}%
        </span>
      </div>

      {/* Content */}
      <div className="p-4 flex flex-col gap-2 flex-1">
        <h3 className="text-white font-semibold text-base leading-snug">{recipe.recipe_title}</h3>

        {recipe.recipe_description && (
          <p className="text-slate-400 text-sm line-clamp-2">{recipe.recipe_description}</p>
        )}

        {/* Missing ingredients hint */}
        {(isLocked || isAlmost) && recipe.missing_ingredients.length > 0 && (
          <p className="text-xs text-slate-500 mt-1">
            Missing: {recipe.missing_ingredients.slice(0, 3).join(', ')}
            {recipe.missing_ingredients.length > 3 && ` +${recipe.missing_ingredients.length - 3} more`}
          </p>
        )}

        {/* Cook button — only active when unlocked */}
        {!isLocked && (
          <div className="mt-auto pt-2">
            <button
              disabled={isAlmost}
              className={`w-full py-2 rounded-lg text-sm font-medium transition-colors ${
                isAlmost
                  ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white cursor-pointer'
              }`}
            >
              Cook
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
