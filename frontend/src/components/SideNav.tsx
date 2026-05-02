import { NavLink } from 'react-router-dom'
import { Package, ChefHat } from 'lucide-react'
import Paths from '../interfaces/Pages'

const navItems = [
  { path: Paths.inventory.path, label: 'Inventory', icon: Package },
  { path: Paths.cookableRecipes.path, label: 'Recipes', icon: ChefHat },
]

export default function SideNav() {
  return (
    <aside className="w-64 h-dvh flex flex-col bg-white border-r border-edge shrink-0">
      <div className="px-7 pt-8 pb-6">
        <h1 className="font-display text-2xl font-bold text-black leading-tight">Kitchen</h1>
        <p className="text-xs text-muted mt-1 tracking-wide">Inventory & Recipes</p>
      </div>

      <nav className="flex-1 px-4">
        {navItems.map(({ path, label, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              `flex items-center gap-3.5 px-4 py-3.5 rounded-xl text-sm font-medium transition-colors mb-1 ${
                isActive
                  ? 'bg-accent-dim text-accent'
                  : 'text-muted hover:text-black hover:bg-[#f7f4f1]'
              }`
            }
          >
            <Icon size={19} strokeWidth={1.8} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-7 pb-8 text-xs text-subtle">
        v0.1
      </div>
    </aside>
  )
}
