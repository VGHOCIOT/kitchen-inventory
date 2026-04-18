import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { ChefHat, Minus, Plus, Timer, ExternalLink, ArrowRightLeft, Ban } from 'lucide-react'
import { fetchRecipeInstructions, fetchCookPlan, cookRecipe } from '../api/recipes'
import type { RecipeOut, CookResponse, CookPlan, CookPlanIngredient } from '../interfaces/Recipes'
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
  const [cookPlan, setCookPlan] = useState<CookPlan | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [scale, setScale] = useState(1)
  const [cookResult, setCookResult] = useState<CookResponse | null>(null)
  const [cooking, setCooking] = useState(false)
  const [wakeLock, setWakeLock] = useState<WakeLockSentinel | null>(null)

  // ingredient_id → substitute_ingredient_id (empty string = use original)
  const [selectedSubs, setSelectedSubs] = useState<Record<string, string>>({})
  // ingredient_ids the user has chosen to skip
  const [skipped, setSkipped] = useState<Set<string>>(new Set())

  const recipeId = window.location.pathname.split('/').pop() || ''

  useEffect(() => {
    if (!recipeId) {
      setError('No recipe ID provided')
      setLoading(false)
      return
    }
    Promise.all([
      fetchRecipeInstructions(recipeId),
      fetchCookPlan(recipeId),
    ])
      .then(([recipeData, plan]) => {
        setRecipe(recipeData.recipe)
        setCookPlan(plan)
        const autoSubs: Record<string, string> = {}
        const autoSkipped = new Set<string>()
        for (const ing of plan.ingredients) {
          if (ing.status !== 'available') {
            if (ing.substitutes.length > 0) {
              autoSubs[ing.ingredient_id] = ing.substitutes[0].substitute_ingredient_id
            } else {
              autoSkipped.add(ing.ingredient_id)
            }
          }
        }
        setSelectedSubs(autoSubs)
        setSkipped(autoSkipped)
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
      // Build substitutions map: only entries where a sub is selected (non-empty)
      const substitutions: Record<string, string> = {}
      for (const [ingId, subId] of Object.entries(selectedSubs)) {
        if (subId) substitutions[ingId] = subId
      }
      const result = await cookRecipe(recipeId, substitutions, Array.from(skipped), scale)
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

      {cookPlan && (
        <CookPlanView
          plan={cookPlan}
          scale={scale}
          selectedSubs={selectedSubs}
          skipped={skipped}
          onScaleChange={setScale}
          onSubChange={(ingId, subId) => setSelectedSubs(prev => ({ ...prev, [ingId]: subId }))}
          onSkipToggle={(ingId) => setSkipped(prev => {
            const next = new Set(prev)
            next.has(ingId) ? next.delete(ingId) : next.add(ingId)
            return next
          })}
        />
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

function CookPlanView({
  plan,
  scale,
  selectedSubs,
  skipped,
  onScaleChange,
  onSubChange,
  onSkipToggle,
}: {
  plan: CookPlan
  scale: number
  selectedSubs: Record<string, string>
  skipped: Set<string>
  onScaleChange: (s: number) => void
  onSubChange: (ingId: string, subId: string) => void
  onSkipToggle: (ingId: string) => void
}) {
  const globalMaxScale = useMemo(() => {
    const limits = plan.ingredients
      .filter(ing => !skipped.has(ing.ingredient_id))
      .map(ing => {
        const selectedSubId = selectedSubs[ing.ingredient_id]
        if (selectedSubId) {
          const sub = ing.substitutes.find(s => s.substitute_ingredient_id === selectedSubId)
          if (sub && sub.max_scale !== null) return sub.max_scale
        }
        return ing.max_scale
      })
      .filter((v): v is number => v !== null)
    return limits.length > 0 ? Math.min(...limits) : Infinity
  }, [plan.ingredients, skipped, selectedSubs])

  const atCap = scale + 0.5 > globalMaxScale

  return (
    <div className="rounded border border-edge p-4 bg-white mb-6">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-muted uppercase tracking-widest">Ingredients</h2>
        <div className="flex items-center gap-2">
          {globalMaxScale !== Infinity && (
            <span className="text-xs text-muted">max {globalMaxScale.toFixed(1)}×</span>
          )}
          <button
            onClick={() => onScaleChange(Math.max(0.5, scale - 0.5))}
            className="p-1 rounded border border-edge text-muted hover:text-black"
          >
            <Minus size={14} />
          </button>
          <span className="text-sm font-medium text-black w-10 text-center">{scale}×</span>
          <button
            onClick={() => onScaleChange(scale + 0.5)}
            disabled={atCap}
            className="p-1 rounded border border-edge text-muted hover:text-black disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <Plus size={14} />
          </button>
        </div>
      </div>
      <ul className="space-y-2">
        {plan.ingredients.map(ing => (
          <CookPlanRow
            key={ing.ingredient_id}
            ing={ing}
            scale={scale}
            selectedSubId={selectedSubs[ing.ingredient_id] ?? ''}
            isSkipped={skipped.has(ing.ingredient_id)}
            onSubChange={(subId) => onSubChange(ing.ingredient_id, subId)}
            onSkipToggle={() => onSkipToggle(ing.ingredient_id)}
          />
        ))}
      </ul>
    </div>
  )
}

function CookPlanRow({
  ing,
  scale,
  selectedSubId,
  isSkipped,
  onSubChange,
  onSkipToggle,
}: {
  ing: CookPlanIngredient
  scale: number
  selectedSubId: string
  isSkipped: boolean
  onSubChange: (subId: string) => void
  onSkipToggle: () => void
}) {
  const displayName = ing.display_name

  const activeSub = selectedSubId
    ? ing.substitutes.find(s => s.substitute_ingredient_id === selectedSubId)
    : null

  const effectiveMaxScale = activeSub ? activeSub.max_scale : ing.max_scale
  const isOverScale = !isSkipped && effectiveMaxScale !== null && scale > effectiveMaxScale

  const rowClass = isSkipped
    ? 'opacity-40 line-through'
    : ing.status === 'available' && !isOverScale
    ? ''
    : ing.status === 'available' && isOverScale
    ? 'text-warn'
    : activeSub
    ? 'text-warn'
    : 'text-danger'

  return (
    <li className={`text-sm flex flex-col gap-1 ${rowClass}`}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-1.5 min-w-0">
          {ing.status !== 'available' && activeSub && (
            <ArrowRightLeft size={12} className="shrink-0 text-warn" />
          )}
          <span className={`${isSkipped ? 'line-through text-muted' : 'text-black'}`}>
            {activeSub ? activeSub.substitute_ingredient_name : displayName}
          </span>
          {ing.status !== 'available' && !activeSub && !isSkipped && (
            <span className="text-xs text-danger ml-1">({ing.status})</span>
          )}
          {isOverScale && ing.status === 'available' && (
            <span className="text-xs text-warn ml-1">(not enough at {scale}×)</span>
          )}
        </div>
        <div className="flex items-center gap-2 shrink-0">
          
          {activeSub && activeSub.substitute_quantity != null && activeSub.substitute_unit ? (
            <span className="text-muted">{formatQty(activeSub.substitute_quantity, scale)} {activeSub.substitute_unit}</span>
          ) : ing.quantity != null && ing.unit && (
            <span className="text-muted">{formatQty(ing.quantity, scale)} {ing.unit}</span>
          )}
          <button
            onClick={onSkipToggle}
            title={isSkipped ? 'Include ingredient' : 'Do not use'}
            className={`p-0.5 rounded transition-colors ${isSkipped ? 'text-danger' : 'text-muted hover:text-danger'}`}
          >
            <Ban size={13} />
          </button>
        </div>
      </div>

      {ing.status !== 'available' && ing.substitutes.length > 0 && !isSkipped && (
        <div className="flex items-center gap-1.5 pl-4 flex-wrap">
          <span className="text-xs text-muted shrink-0">Sub:</span>
          <button
            onClick={() => onSubChange('')}
            className={`text-xs px-2 py-0.5 rounded-full border transition-colors ${
              !selectedSubId
                ? 'bg-muted/10 border-muted text-muted font-medium'
                : 'border-edge text-muted hover:border-muted'
            }`}
          >
            {ing.ingredient_name}
          </button>
          {ing.substitutes.map(s => (
            <button
              key={s.substitute_ingredient_id}
              onClick={() => onSubChange(s.substitute_ingredient_id)}
              className={`text-xs px-2 py-0.5 rounded-full border transition-colors ${
                selectedSubId === s.substitute_ingredient_id
                  ? 'bg-warn/10 border-warn text-warn font-medium'
                  : 'border-edge text-muted hover:border-warn hover:text-warn'
              }`}
            >
              {s.substitute_ingredient_name}
            </button>
          ))}
        </div>
      )}
    </li>
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
                  : `bg-gray-100 text-muted ${isChecked ? '' : 'hover:text-black'}`
              }`}
              disabled={isChecked}
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
