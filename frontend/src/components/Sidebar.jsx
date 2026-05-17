import { NavLink } from 'react-router-dom'
import { ROUTES } from '../utils/constants'

const navItems = [
  { label: 'Dashboard', to: ROUTES.DASHBOARD },
  { label: 'Import', to: ROUTES.IMPORT },
]

export default function Sidebar() {
  return (
    <aside className="glass w-64 rounded-xl p-4">
      <h2 className="mb-4 text-xl font-bold">DMS Email Monitor</h2>
      <nav className="space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `block rounded-lg px-3 py-2 transition ${isActive ? 'bg-electric/30 text-white' : 'text-white/75 hover:bg-white/10'}`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
