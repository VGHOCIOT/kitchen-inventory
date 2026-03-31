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
  match_type: string
  availability_percent: number
  ingredient_availability: IngredientAvailability[]
  missing_ingredients: string[]
  suggested_substitutions: SubstitutionSuggestion[]
}

export interface RecipeMatchResponse {
  can_make_now: RecipeMatchResult[]
  missing_one: RecipeMatchResult[]
  missing_few: RecipeMatchResult[]
  with_substitutions: RecipeMatchResult[]
  total_recipes_checked: number
}
