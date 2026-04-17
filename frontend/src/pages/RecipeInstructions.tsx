import { useState, useEffect, useRef, useCallback } from 'react'
import { ChefHat, Minus, Plus, Timer, ExternalLink } from 'lucide-react'
import { fetchRecipeInstructions, cookRecipe } from '../api/recipes'
import type { RecipeOut, RecipeIngredient, CookResponse } from '../interfaces/Recipes'
import { useDispatch } from 'react-redux'
import { AppDispatch } from '../store'
import RecipeActions from '../store/actions/recipeActions'
import InventoryActions from '../store/actions/inventoryActions'

function parseTimer(text: string): number | null {
  const patterns = [
    /(\d+)\s*(?:to\s*\d+\s*)?hours?/i,
    /(\d+)\s*(?:to\s*\d+\s*)?minutes?/i,
    /(\d+)\s*(?:to\s*\d+\s*)?mins?/i,
  ]
  for (const pattern of patterns) {
    const match = text.match(pattern)
    if (match) {
      const val = parseInt(match[1])
      if (/hours?/i.test(match[0])) return val * 60
      return val
    }
  }
  return null
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatQty(qty: number, scale: number): string {
  const scaled = qty * scale
  if (scaled % 1 === 0) return scaled.toString()
  return scaled.toFixed(1).replace(/\.0$/, '')
}

export default function RecipeInstructions() {
  const dispatch = useDispatch<AppDispatch>()
  const [recipe, setRecipe] = useState<RecipeOut | null>(null)
  const [ingredients, setIngredients] = useState<RecipeIngredient[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [scale, setScale] = useState(1)
  const [cookResult, setCookResult] = useState<CookResponse | null>(null)
  const [cooking, setCooking] = useState(false)
  const [wakeLock, setWakeLock] = useState<WakeLockSentinel | null>(null)

  const recipeId = window.location.pathname.split('/').pop() || ''

  useEffect(() => {
    if (!recipeId) {
      setError('No recipe ID provided')
      setLoading(false)
      return
    }
    fetchRecipeInstructions(recipeId)
      .then((data) => {
        setRecipe(data.recipe)
        setIngredients(data.ingredients)
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false))
  }, [recipeId])

  useEffect(() => {
    const requestWakeLock = async () => {
      try {
        if ('wakeLock' in navigator) {
          const lock = await navigator.wakeLock.request('screen')
          setWakeLock(lock)
        }
      } catch { /* user denied or unsupported */ }
    }
    requestWakeLock()
    return () => { wakeLock?.release() }
  }, [])

  const handleCook = async () => {
    if (!recipeId || cooking) return
    setCooking(true)
    try {
      const result = await cookRecipe(recipeId)
      setCookResult(result)
      dispatch(InventoryActions.fetchInventory())
      dispatch(RecipeActions.fetchRecipeMatches())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Cook failed')
    } finally {
      setCooking(false)
    }
  }

  if (loading) return <p className="p-6 text-muted">Loading recipe…</p>
  if (error) return <p className="p-6 text-danger">{error}</p>
  if (!recipe) return null

  return (
    <div className="p-6 max-w-4xl mx-auto bg-white">
      <h1 className="text-3xl font-bold mb-2 text-black">{recipe.title}</h1>

      {recipe.source_url && (
        <a href={recipe.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-sm text-accent hover:text-accent-hover mb-6">
          <ExternalLink size={14} />
          Original recipe
        </a>
      )}

      {recipe.image_url && (
        <img
          src={recipe.image_url}
          alt={recipe.title}
          className="w-full max-h-72 object-cover rounded mb-6 border border-edge"
        />
      )}

      {recipe.description && (
        <p className="text-muted text-sm mb-6">{recipe.description}</p>
      )}

      {ingredients.length > 0 && (
        <div className="rounded border border-edge p-4 bg-white mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-muted uppercase tracking-widest">Ingredients</h2>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setScale(s => Math.max(0.5, s - 0.5))}
                className="p-1 rounded border border-edge text-muted hover:text-black"
              >
                <Minus size={14} />
              </button>
              <span className="text-sm font-medium text-black w-10 text-center">{scale}x</span>
              <button
                onClick={() => setScale(s => s + 0.5)}
                className="p-1 rounded border border-edge text-muted hover:text-black"
              >
                <Plus size={14} />
              </button>
            </div>
          </div>
          <ul className="space-y-1.5">
            {ingredients.map(ing => (
              <li key={ing.id} className="text-sm text-black flex justify-between">
                <span>{ing.ingredient_text.replace(/^[\d\s/.½¼¾⅓⅔]+/, '').trim()}</span>
                {ing.quantity != null && ing.unit && (
                  <span className="text-muted shrink-0 ml-3">{formatQty(ing.quantity, scale)} {ing.unit}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="rounded border border-edge p-4 bg-white mb-6">
        <h2 className="text-sm font-semibold text-muted uppercase tracking-widest mb-3">Steps</h2>
        <div className="flex flex-col">
          {recipe.instructions.map((step, index) => (
            <InstructionStep key={index} step={step} index={index} />
          ))}
        </div>
      </div>

      {cookResult ? (
        <CookResultSummary result={cookResult} />
      ) : (
        <button
          onClick={handleCook}
          disabled={cooking}
          className="w-full py-3 rounded-lg text-sm font-medium transition-colors bg-accent hover:bg-accent-hover text-canvas cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <ChefHat size={18} />
          {cooking ? 'Deducting from inventory…' : 'Cook — deduct from inventory'}
        </button>
      )}
    </div>
  )
}

function InstructionStep({ step, index }: { step: string; index: number }) {
  const [isChecked, setIsChecked] = useState(false)
  const timerMinutes = parseTimer(step)
  const [countdown, setCountdown] = useState<number | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const startTimer = useCallback((minutes: number) => {
    if (intervalRef.current) clearInterval(intervalRef.current)
    setCountdown(minutes * 60)
    intervalRef.current = setInterval(() => {
      setCountdown(prev => {
        if (prev === null || prev <= 1) {
          clearInterval(intervalRef.current!)
          intervalRef.current = null
          return 0
        }
        return prev - 1
      })
    }, 1000)
  }, [])

  useEffect(() => {
    return () => { if (intervalRef.current) clearInterval(intervalRef.current) }
  }, [])

  return (
    <div className={`flex w-full rounded-md p-3 border-b items-start justify-between last:border-0 gap-3 transition-all duration-200 ${isChecked ? 'opacity-40' : ''}`}>
      <div className="flex items-start gap-3 flex-1 min-w-0">
        <span className="text-xs font-semibold text-muted mt-0.5 shrink-0 w-5">{index + 1}</span>
        <div className="flex flex-col gap-1.5 flex-1 min-w-0">
          <span className={`text-sm text-slate-800 ${isChecked ? 'line-through decoration-slate-400' : ''}`}>
            {step}
          </span>
          {timerMinutes && (
            <button
              onClick={() => countdown === null ? startTimer(timerMinutes) : setCountdown(null)}
              className={`inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full w-fit transition-colors ${
                countdown !== null
                  ? countdown === 0
                    ? 'bg-danger/10 text-danger animate-pulse'
                    : 'bg-accent-dim text-accent'
                  : 'bg-gray-100 text-muted hover:text-black'
              }`}
            >
              <Timer size={12} />
              {countdown !== null ? formatTime(countdown) : `${timerMinutes} min`}
            </button>
          )}
        </div>
      </div>
      <label className="flex items-center cursor-pointer relative shrink-0 mt-0.5">
        <input
          type="checkbox"
          checked={isChecked}
          onChange={() => setIsChecked(!isChecked)}
          className="peer h-5 w-5 cursor-pointer transition-all appearance-none rounded shadow hover:shadow-md border border-slate-300 checked:bg-accent checked:border-accent"
        />
        <span className="absolute text-white opacity-0 peer-checked:opacity-100 top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 pointer-events-none">
          <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor" stroke="currentColor" strokeWidth="1">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
          </svg>
        </span>
      </label>
    </div>
  )
}

function CookResultSummary({ result }: { result: CookResponse }) {
  return (
    <div className="rounded border border-edge p-4 bg-white">
      <h2 className="text-sm font-semibold text-accent uppercase tracking-widest mb-3">Cooked — {result.recipe_title}</h2>
      {result.deducted.length > 0 && (
        <div className="mb-2">
          <p className="text-xs text-muted mb-1">Deducted from inventory:</p>
          <ul className="space-y-0.5">
            {result.deducted.map((d, i) => (
              <li key={i} className="text-sm text-black">{d.ingredient}: {d.amount} {d.unit}</li>
            ))}
          </ul>
        </div>
      )}
      {result.failed.length > 0 && (
        <div>
          <p className="text-xs text-muted mb-1">Could not deduct:</p>
          <p className="text-sm text-danger">{result.failed.join(', ')}</p>
        </div>
      )}
    </div>
  )
}
