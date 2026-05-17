import { createContext, useCallback, useEffect, useMemo, useState } from 'react'

const THEMES = {
  dark: {
    name: 'dark',
    bg: '#0a0e27',
    bgSecondary: '#111638',
    surface: 'rgba(255,255,255,0.08)',
    surfaceHover: 'rgba(255,255,255,0.12)',
    border: 'rgba(255,255,255,0.15)',
    text: '#ffffff',
    textSecondary: 'rgba(255,255,255,0.7)',
    textMuted: 'rgba(255,255,255,0.5)',
    accent: '#667eea',
    accentLight: '#818cf8',
    success: '#10b981',
    warning: '#f59e0b',
    danger: '#ef4444',
    info: '#3b82f6',
  },
  light: {
    name: 'light',
    bg: '#f0f2f5',
    bgSecondary: '#ffffff',
    surface: 'rgba(255,255,255,0.9)',
    surfaceHover: 'rgba(255,255,255,1)',
    border: 'rgba(0,0,0,0.1)',
    text: '#1a1a2e',
    textSecondary: 'rgba(0,0,0,0.65)',
    textMuted: 'rgba(0,0,0,0.4)',
    accent: '#667eea',
    accentLight: '#818cf8',
    success: '#059669',
    warning: '#d97706',
    danger: '#dc2626',
    info: '#2563eb',
  },
}

export const ThemeContext = createContext({
  theme: THEMES.dark,
  themeName: 'dark',
  toggleTheme: () => {},
})

export function ThemeProvider({ children }) {
  const [themeName, setThemeName] = useState(() => {
    return localStorage.getItem('dms-theme') || 'dark'
  })

  const theme = useMemo(() => THEMES[themeName] || THEMES.dark, [themeName])

  const toggleTheme = useCallback(() => {
    setThemeName((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark'
      localStorage.setItem('dms-theme', next)
      return next
    })
  }, [])

  useEffect(() => {
    const root = document.documentElement
    Object.entries(theme).forEach(([key, value]) => {
      if (key !== 'name') {
        root.style.setProperty(`--theme-${key}`, value)
      }
    })
    root.setAttribute('data-theme', themeName)
  }, [theme, themeName])

  const value = useMemo(() => ({ theme, themeName, toggleTheme }), [theme, themeName, toggleTheme])

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}
