import { type PayloadAction } from '@reduxjs/toolkit'
import { RecipeMatchResponse, RecipeMatchResult } from '../../interfaces/Recipes'

export const setRecipeMatches = (state: RecipeMatchResponse, action: PayloadAction<RecipeMatchResponse>): RecipeMatchResponse => {
  return {
    ...state,
    unlocked: action.payload.unlocked,
    almost: action.payload.almost,
    locked: action.payload.locked,
    total_recipes_checked: action.payload.total_recipes_checked,
  }
}

export const updateRecipeMatch = (state: RecipeMatchResponse, action: PayloadAction<RecipeMatchResult>): RecipeMatchResponse => {
  const updated = action.payload
  const allRecipes = [...state.unlocked, ...state.almost, ...state.locked]
  const index = allRecipes.findIndex(r => r.recipe_id === updated.recipe_id)
  if (index === -1) return state // not found, ignore

  // Remove from current category
  let newState = { ...state, unlocked: state.unlocked.filter(r => r.recipe_id !== updated.recipe_id), almost: state.almost.filter(r => r.recipe_id !== updated.recipe_id), locked: state.locked.filter(r => r.recipe_id !== updated.recipe_id) }

  // Add to new category
  if (updated.match_type === 'unlocked') {
    newState.unlocked = [...newState.unlocked, updated]
  } else if (updated.match_type === 'almost') {
    newState.almost = [...newState.almost, updated]
  } else {
    newState.locked = [...newState.locked, updated]
  }

  return newState
}

