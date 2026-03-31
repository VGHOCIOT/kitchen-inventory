import { useState, useEffect } from 'react'
import type { RecipeMatchResponse, RecipeMatchResult } from '../interfaces/Recipes'

async function fetchMatchedRecipes(): Promise<RecipeMatchResponse> {
  const res = await fetch('/api/v1/recipes/match-inventory')
  if (!res.ok) throw new Error(`Failed to fetch recipes: ${res.status}`)
  return res.json()
}

const CATEGORY_LABELS: Record<keyof Omit<RecipeMatchResponse, 'total_recipes_checked'>, string> = {
  can_make_now: 'Ready to Cook',
  missing_one: 'Missing One Ingredient',
  missing_few: 'Missing a Few',
  with_substitutions: 'With Substitutions',
}

const CATEGORY_KEYS = Object.keys(CATEGORY_LABELS) as Array<
  keyof Omit<RecipeMatchResponse, 'total_recipes_checked'>
>

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

  if (loading) {
    return (
      <p style={{ padding: '24px', color: 'var(--text-muted)', textAlign: 'center' }}>
        Loading recipes...
      </p>
    )
  }

  if (error) {
    return (
      <p style={{ padding: '24px', color: 'var(--danger)', textAlign: 'center' }}>
        {error}
      </p>
    )
  }

  if (!data) return null

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100dvh', overflowY: 'auto' }}>
      {CATEGORY_KEYS.map(key => {
        const recipes: RecipeMatchResult[] = data[key]
        if (recipes.length === 0) return null
        return (
          <section key={key} style={{ padding: '16px 0' }}>
            <h2 style={{
              padding: '8px 20px',
              fontSize: '0.75rem',
              fontWeight: 700,
              letterSpacing: '0.08em',
              color: 'var(--text-muted)',
            }}>
              {CATEGORY_LABELS[key].toUpperCase()} ({recipes.length})
            </h2>
            {recipes.map(recipe => (
              <RecipeCard key={recipe.recipe_id} recipe={recipe} />
            ))}
          </section>
        )
      })}
      {data.total_recipes_checked === 0 && (
        <p style={{ padding: '24px', color: 'var(--text-muted)', textAlign: 'center' }}>
          No recipes saved yet.
        </p>
      )}
    </div>
  )
}

function RecipeCard({ recipe }: { recipe: RecipeMatchResult }) {
  return (
    <div style={{
      padding: '14px 20px',
      borderBottom: '1px solid var(--border)',
      minHeight: '56px',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '1rem' }}>{recipe.recipe_title}</span>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', flexShrink: 0, marginLeft: '12px' }}>
          {Math.round(recipe.availability_percent)}%
        </span>
      </div>
      {recipe.missing_ingredients.length > 0 && (
        <p style={{ margin: '4px 0 0', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Missing: {recipe.missing_ingredients.join(', ')}
        </p>
      )}
    </div>
  )
}
