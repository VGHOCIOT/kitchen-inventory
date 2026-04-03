import { createSlice } from '@reduxjs/toolkit';
import { RecipeMatchResponse } from '../../interfaces/Recipes';
import * as reducers from '../reducers/recipeReducers';

const initialState: RecipeMatchResponse = {
  unlocked: [],
  almost: [],
  locked: [],
  total_recipes_checked: 0,
};

const slice = createSlice({
  name: 'recipes',
  initialState,
  reducers,
});

export default slice.reducer;
export const actions = slice.actions;