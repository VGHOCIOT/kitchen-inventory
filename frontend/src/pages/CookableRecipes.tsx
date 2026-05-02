import { useState } from 'react'
import { Lock, ArrowRightLeft, Plus, X } from 'lucide-react'
import type { RecipeMatchResult } from '../interfaces/Recipes'
import { useSelector } from 'react-redux'
import { RootState } from '../store'
import { createRecipeFromUrl } from '../api/recipes'

function AddRecipeModal({ onClose }: { onClose: () => void }) {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!url.trim() || loading) return
    setLoading(true)
    setError(null)
    try {
      await createRecipeFromUrl(url.trim())
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display text-lg font-semibold text-black">Add Recipe from URL</h2>
          <button onClick={onClose} className="text-muted hover:text-black transition-colors cursor-pointer">
            <X size={20} />
          </button>
        </div>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="url"
            placeholder="https://..."
            value={url}
            onChange={e => setUrl(e.target.value)}
            autoFocus
            className="w-full border border-edge rounded-lg px-3 py-2 text-sm text-black placeholder:text-subtle focus:outline-none focus:ring-2 focus:ring-accent"
          />
          {error && <p className="text-sm text-red-500">{error}</p>}
          <button
            type="submit"
            disabled={!url.trim() || loading}
            className="w-full py-2 rounded-lg text-sm font-medium bg-accent hover:bg-accent-hover text-canvas transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Importing…' : 'Import Recipe'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default function CookableRecipes() {
  const recipeState = useSelector((state: RootState) => state.recipes)
  const [addOpen, setAddOpen] = useState(false)

  const Section = ({ title, recipes }: { title: string; recipes: RecipeMatchResult[] }) => {
    if (recipes.length === 0) return null
    return (
      <section className="mb-10">
        <h2 className="font-display text-sm font-semibold text-muted mb-4 uppercase tracking-widest">{title}</h2>
        <div className="grid grid-cols-2 gap-4">
          {recipes.map(recipe => (
            <RecipeCard key={recipe.recipe_id} recipe={recipe} />
          ))}
        </div>
      </section>
    )
  }

  return (
    <div className="h-full overflow-y-auto bg-white">
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="font-display text-3xl font-bold text-black">Cookable Recipes</h1>
        <button
          onClick={() => setAddOpen(true)}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-accent hover:bg-accent-hover text-white transition-colors cursor-pointer"
        >
          <Plus size={16} />
          Add Recipe
        </button>
      </div>
      <Section title="Unlocked" recipes={recipeState.unlocked} />
      <Section title="Almost There" recipes={recipeState.almost} />
      <Section title="Locked" recipes={recipeState.locked} />
    </div>
    {addOpen && <AddRecipeModal onClose={() => setAddOpen(false)} />}
    </div>
  )
}

export function RecipeCard({ recipe }: { recipe: RecipeMatchResult }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const isLocked = recipe.match_type === 'locked'
  const isAlmost = recipe.match_type === 'almost'
  const hasSubs = recipe.suggested_substitutions.length > 0

  const badgeClass = isLocked
    ? 'bg-surface text-muted'
    : isAlmost
    ? 'bg-warn-dim text-warn'
    : 'bg-accent-dim text-accent'

  return (
    <div className={`relative rounded overflow-hidden bg-surface border border-edge bg-white flex flex-col ${isLocked ? 'opacity-60' : ''}`}>
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

        {isLocked && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
            <div className="bg-canvas/80 p-3 rounded-full">
              <Lock size={28} className="text-muted" />
            </div>
          </div>
        )}

        <span className={`absolute top-2 right-2 text-xs font-semibold px-2 py-1 rounded-full ${badgeClass}`}>
          {Math.round(recipe.availability_percent)}%
        </span>
      </div>

      <div className="p-4 flex flex-col gap-2 flex-1">
        <h3 className="font-display font-semibold text-base leading-snug text-black">{recipe.recipe_title}</h3>

        {recipe.recipe_description && (
          <p className="text-muted text-sm line-clamp-2">{recipe.recipe_description}</p>
        )}

        {hasSubs && (
          <div className="flex flex-col gap-1 mt-1">
            {recipe.suggested_substitutions.map(sub => (
              <div key={sub.original_ingredient_id} className="flex items-center gap-1.5 text-xs text-accent">
                <ArrowRightLeft size={12} className="shrink-0" />
                <span>{sub.original_ingredient_name} → {sub.substitute_ingredient_name}</span>
              </div>
            ))}
          </div>
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
              className="w-full py-2 rounded-lg text-sm font-medium transition-colors bg-accent hover:bg-accent-hover text-white cursor-pointer"
              onClick={() => window.location.href = `/recipes/${recipe.recipe_id}`}
            >
              Cook
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
