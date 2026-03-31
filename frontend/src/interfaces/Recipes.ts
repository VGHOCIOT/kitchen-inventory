export interface IngredientAvailability {
  ingredient_id: string
  ingredient_name: string
  required_quantity: number
  available_quantity: number
  unit: string
  is_sufficient: boolean
}

export interface SubstitutionSuggestion {
  original_ingredient_id: string
  original_ingredient_name: string
  substitute_ingredient_id: string
  substitute_ingredient_name: string
  ratio: number
  quality_score: number
  notes: string | null
}

export interface RecipeMatchResult {
  recipe_id: string
  recipe_title: string
  recipe_description: string | null
  recipe_image_url: string | null
  match_type: 'unlocked' | 'almost' | 'locked'
  availability_percent: number  // substitutions count as covered
  ingredient_availability: IngredientAvailability[]
  missing_ingredients: string[]  // only ingredients with no inventory and no substitution
  suggested_substitutions: SubstitutionSuggestion[]
}

export interface RecipeMatchResponse {
  unlocked: RecipeMatchResult[]   // 100%
  almost: RecipeMatchResult[]     // >= 70%, substitutions count
  locked: RecipeMatchResult[]     // < 70%
  total_recipes_checked: number
}
