import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ROUTES } from '../utils/constants'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState('')

  const onSubmit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      await login(form)
      navigate(ROUTES.DASHBOARD)
    } catch {
      setError('Login failed. Please verify your credentials.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md glow">
        <h1 className="mb-2 text-2xl font-bold">Sign in</h1>
        <p className="mb-6 text-sm text-white/70">Contract lifecycle intelligence for legal teams.</p>
        <form className="space-y-3" onSubmit={onSubmit}>
          <Input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
            required
          />
          <Input
            type="password"
            placeholder="Password"
            value={form.password}
            onChange={(e) => setForm((prev) => ({ ...prev, password: e.target.value }))}
            required
          />
          {error && <p className="text-sm text-red-300">{error}</p>}
          <Button className="w-full" type="submit">
            Login
          </Button>
        </form>
        <p className="mt-4 text-sm text-white/70">
          No account?{' '}
          <Link className="text-electric hover:underline" to={ROUTES.REGISTER}>
            Register
          </Link>
        </p>
      </Card>
    </div>
  )
}
