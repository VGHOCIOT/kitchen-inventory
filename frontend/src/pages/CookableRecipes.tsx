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

  if (loading) return <p className="p-6 text-muted">Loading recipes…</p>
  if (error) return <p className="p-6 text-danger">{error}</p>
  if (!data) return null

  const Section = ({ title, recipes }: { title: string; recipes: RecipeMatchResult[] }) => {
    if (recipes.length === 0) return null
    return (
      <section className="mb-10">
        <h2 className="text-sm font-semibold text-muted mb-4 uppercase tracking-widest">{title}</h2>
        <div className="grid grid-cols-2 gap-4">
          {recipes.map(recipe => (
            <RecipeCard key={recipe.recipe_id} recipe={recipe} />
          ))}
        </div>
      </section>
    )
  }

  return (
    <div className="p-6 max-w-4xl mx-auto bg-white">
      <h1 className="text-3xl font-bold text-text mb-8 text-black">Cookable Recipes</h1>
      <Section title="Unlocked" recipes={data.unlocked} />
      <Section title="Almost There" recipes={data.almost} />
      <Section title="Locked" recipes={data.locked} />
    </div>
  )
}

export function RecipeCard({ recipe }: { recipe: RecipeMatchResult }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const isLocked = recipe.match_type === 'locked'
  const isAlmost = recipe.match_type === 'almost'

  const badgeClass = isLocked
    ? 'bg-surface text-muted'
    : isAlmost
    ? 'bg-warn-dim text-warn'
    : 'bg-accent-dim text-accent'

  return (
    <div className={`relative rounded overflow-hidden bg-surface border border-border bg-white flex flex-col ${isLocked ? 'opacity-60' : ''}`}>
      {/* Image */}
      <div className="relative h-48">
        {recipe.recipe_image_url ? (
          <img
            src={recipe.recipe_image_url}
            alt={recipe.recipe_title}
            className={`w-full h-full object-cover ${isLocked ? 'grayscale' : ''}`}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-subtle text-sm">No image</div>
        )}

        {/* Lock overlay */}
        {isLocked && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
            <div className="bg-bg/80 p-3 rounded-full">
              <Lock size={28} className="text-muted" />
            </div>
          </div>
        )}

        {/* Availability badge */}
        <span className={`absolute top-2 right-2 text-xs font-semibold px-2 py-1 rounded-full ${badgeClass}`}>
          {Math.round(recipe.availability_percent)}%
        </span>
      </div>

      {/* Content */}
      <div className="p-4 flex flex-col gap-2 flex-1">
        <h3 className="text-text font-semibold text-base leading-snug text-black">{recipe.recipe_title}</h3>

        {recipe.recipe_description && (
          <p className="text-muted text-sm line-clamp-2">{recipe.recipe_description}</p>
        )}

        {(isLocked || isAlmost) && recipe.missing_ingredients.length > 0 && (
          <div className={`relative mt-auto ${recipe.missing_ingredients.length > 3 ? 'cursor-pointer' : ''}`} onClick={() => recipe.missing_ingredients.length > 3 && setIsExpanded(v => !v)}>
            <p className="text-xs invisible">Missing: {recipe.missing_ingredients.join(', ')}</p>
            <p className="text-xs text-subtle absolute bottom-0 left-0 right-0">
              Missing: {
                isExpanded || recipe.missing_ingredients.length <= 3
                  ? recipe.missing_ingredients.join(', ')
                  : `${recipe.missing_ingredients.slice(0, 3).join(', ')} +${recipe.missing_ingredients.length - 3} more`
              }
            </p>
          </div>
        )}

        {!isLocked && (
          <div className="pt-2">
            <button
              disabled={isAlmost}
              className={`w-full py-2 rounded-lg text-sm font-medium transition-colors ${
                isAlmost
                  ? 'bg-raised text-subtle cursor-not-allowed'
                  : 'bg-accent hover:bg-accent-hover text-bg cursor-pointer'
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
