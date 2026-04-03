import { type Dispatch } from '@reduxjs/toolkit'
import { actions } from '../slices/recipeSlice'
import { fetchMatchedRecipes } from '../../api/recipes'

export default class RecipeActions {
    static fetchRecipeMatches = () => async (dispatch: Dispatch) => {
        const data = await fetchMatchedRecipes()
        dispatch(actions.setRecipeMatches(data))
    }

    static updateRecipeMatch = (match: any) => (dispatch: Dispatch) => {
        dispatch(actions.updateRecipeMatch(match))
    }
}