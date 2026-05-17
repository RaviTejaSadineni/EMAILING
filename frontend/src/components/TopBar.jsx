import ThemeToggle from './dashboard/ThemeToggle'
import { useAuth } from '../hooks/useAuth'
import Button from './ui/Button'

export default function TopBar() {
  const { user, logout } = useAuth()

  return (
    <header className="glass mb-4 flex items-center justify-between rounded-xl p-4">
      <div>
        <p className="text-sm text-white/60">Welcome back</p>
        <h1 className="text-xl font-bold">{user?.username || 'Analyst'}</h1>
      </div>
      <div className="flex items-center gap-3">
        <ThemeToggle />
        <Button className="text-sm" onClick={logout}>
          Logout
        </Button>
      </div>
    </header>
  )
}
