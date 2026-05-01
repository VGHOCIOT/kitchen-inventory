import { type ReactElement, useEffect, useRef, useState, useContext, createContext } from 'react'
import {
  createBrowserRouter,
  RouterProvider,
  Outlet,
  type RouteObject
} from 'react-router-dom'
import { useDispatch } from 'react-redux'
import { AppDispatch } from './store'
import InventoryPage from './pages/InventoryPage'
import CookableRecipes from './pages/CookableRecipes'
import RecipeInstructions from './pages/RecipeInstructions'
import ScanConfirmModal from './components/ScanConfirmModal'
import ManualEntryModal from './components/ManualEntryModal'
import Paths from './interfaces/Pages'
import RecipeActions from './store/actions/recipeActions'
import InventoryActions from './store/actions/inventoryActions'
import { scanBarcode } from './api/items'
import type { ScanOut } from './interfaces/Inventory'

// Zebra/Symbol scanners in HID mode emit barcodes as rapid keystrokes ending with Enter.
// Characters arriving within SCAN_TIMEOUT_MS of each other are treated as one scan sequence.
const SCAN_TIMEOUT_MS = 50
const MIN_BARCODE_LENGTH = 6

const DEFAULT_SCAN_LOCATION = 'fridge'

export const ScanContext = createContext<{ openManual: () => void }>({ openManual: () => {} })
export const useScanContext = () => useContext(ScanContext)

function BarcodeLayout() {
  const [pendingScan, setPendingScan] = useState<ScanOut | null>(null)
  const [manualOpen, setManualOpen] = useState(false)
  const bufferRef = useRef<string>('')
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    function flush(barcode: string) {
      if (barcode.length < MIN_BARCODE_LENGTH) return
      scanBarcode({ barcode, location: DEFAULT_SCAN_LOCATION, quantity: null })
        .then(setPendingScan)
        .catch(console.error)
    }

    function onKeyDown(e: KeyboardEvent) {
      // Ignore modifier-key combos (user navigating, not scanning)
      if (e.ctrlKey || e.altKey || e.metaKey) return

      if (e.key === 'Enter') {
        if (timerRef.current) clearTimeout(timerRef.current)
        const barcode = bufferRef.current
        bufferRef.current = ''
        flush(barcode)
        return
      }

      if (e.key.length === 1) {
        bufferRef.current += e.key
        if (timerRef.current) clearTimeout(timerRef.current)
        timerRef.current = setTimeout(() => {
          bufferRef.current = ''
        }, SCAN_TIMEOUT_MS)
      }
    }

    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  return (
    <ScanContext.Provider value={{ openManual: () => setManualOpen(true) }}>
      <Outlet />
      {pendingScan && (
        pendingScan.requires_manual_entry
          ? <ManualEntryModal
              initialName={pendingScan.product_reference.name}
              initialCategories={pendingScan.product_reference.categories}
              initialBrands={pendingScan.product_reference.brands}
              onClose={() => setPendingScan(null)}
            />
          : <ScanConfirmModal scanResult={pendingScan} onClose={() => setPendingScan(null)} />
      )}
      {manualOpen && <ManualEntryModal onClose={() => setManualOpen(false)} />}
    </ScanContext.Provider>
  )
}

const routes: RouteObject[] = [
  {
    element: <BarcodeLayout />,
    children: [
      {
        path: Paths.inventory.path,
        element: <InventoryPage />
      },
      {
        path: Paths.cookableRecipes.path,
        element: <CookableRecipes />
      },
      {
        path: Paths.recipeInstructions.path,
        element: <RecipeInstructions />
      },
    ]
  }
]

const router = createBrowserRouter(routes)

function AppWithStore(): ReactElement {
  const dispatch = useDispatch<AppDispatch>()

  useEffect(() => {
    dispatch(InventoryActions.fetchInventory())
    dispatch(RecipeActions.fetchRecipeMatches())

    const ws = new WebSocket(`ws://${window.location.host}/ws`)

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data)
      if (msg.event === 'item_added' || msg.event === 'item_deleted' || msg.event === 'item_updated' || msg.event === 'recipe_added' || msg.event === 'recipe_deleted') {
        dispatch(InventoryActions.fetchInventory())
        dispatch(RecipeActions.fetchRecipeMatches())
      }
    }

    return () => ws.close()
  }, [dispatch])

  return <RouterProvider router={router} />
}

export default (): ReactElement => (
  <AppWithStore />
)
