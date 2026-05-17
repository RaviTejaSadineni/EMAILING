import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { ROUTES } from '../utils/constants'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Input from '../components/ui/Input'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', username: '', password: '' })
  const [error, setError] = useState('')

  const onSubmit = async (event) => {
    event.preventDefault()
    setError('')
    try {
      await register(form)
      navigate(ROUTES.DASHBOARD)
    } catch {
      setError('Registration failed. Please try again.')
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <h1 className="mb-2 text-2xl font-bold">Create account</h1>
        <form className="space-y-3" onSubmit={onSubmit}>
          <Input
            type="email"
            placeholder="Email"
            value={form.email}
            onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value }))}
            required
          />
          <Input
            placeholder="Username"
            value={form.username}
            onChange={(e) => setForm((prev) => ({ ...prev, username: e.target.value }))}
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
            Register
          </Button>
        </form>
        <p className="mt-4 text-sm text-white/70">
          Already have an account?{' '}
          <Link className="text-electric hover:underline" to={ROUTES.LOGIN}>
            Login
          </Link>
        </p>
      </Card>
    </div>
  )
}
