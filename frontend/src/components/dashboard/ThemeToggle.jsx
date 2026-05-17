import { useTheme } from '../../hooks/useTheme'

export default function ThemeToggle() {
  const { themeName, toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/10 text-lg transition-colors hover:bg-white/20"
      title={`Switch to ${themeName === 'dark' ? 'light' : 'dark'} mode`}
    >
      {themeName === 'dark' ? '☀️' : '🌙'}
    </button>
  )
}
