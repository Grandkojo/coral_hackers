import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiEye, FiEyeOff } from 'react-icons/fi'
import { SiGoogle } from 'react-icons/si'
import type { SignupCredentials } from '../types/auth'

export default function SignupPage() {
  const navigate = useNavigate()
  const [credentials, setCredentials] = useState<SignupCredentials>({
    email: '',
    password: '',
    confirmPassword: '',
    orgName: '',
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setCredentials((prev) => ({ ...prev, [name]: value }))
    if (error) setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!credentials.orgName.trim()) {
      setError('Organization name is required')
      return
    }
    if (!credentials.email) {
      setError('Email is required')
      return
    }
    if (!credentials.password) {
      setError('Password is required')
      return
    }
    if (credentials.password !== credentials.confirmPassword) {
      setError('Passwords do not match')
      return
    }
    if (credentials.password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }

    setIsSubmitting(true)
    console.log('Signup:', {
      orgName: credentials.orgName,
      email: credentials.email,
      password: credentials.password,
    })
    setIsSubmitting(false)
  }

  const handleGoogleSignUp = () => {
    console.log('Google sign-up clicked')
  }

  return (
    <div className="flex items-center justify-center px-4 md:h-screen">
      <div className="w-full py-4 md:py-0" style={{ maxWidth: '480px' }}>
        <div className="card">
          <div className="card-header">
            <div>
              <h1 className="text-lg font-semibold" style={{ color: 'var(--ink)' }}>
                Create Account
              </h1>
              <p className="text-sm" style={{ color: 'var(--ink-2)' }}>
                Set up Reef for your organization
              </p>
            </div>
          </div>

          <div className="p-6 space-y-5">
            {error && (
              <div
                className="p-3 text-sm border"
                style={{
                  background: 'var(--red-dim)',
                  borderColor: 'var(--red)',
                  color: 'var(--red)',
                }}
              >
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid gap-4" style={{ gridTemplateColumns: '1fr 1fr' }}>
                <div className="space-y-2">
                  <label htmlFor="orgName" className="label block">
                    Organization
                  </label>
                  <input
                    id="orgName"
                    name="orgName"
                    type="text"
                    className="field-input"
                    placeholder="Your Company"
                    value={credentials.orgName}
                    onChange={handleChange}
                    disabled={isSubmitting}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <label htmlFor="email" className="label block">
                    Email
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    className="field-input"
                    placeholder="you@company.com"
                    value={credentials.email}
                    onChange={handleChange}
                    disabled={isSubmitting}
                    required
                  />
                </div>
              </div>

              <div className="grid gap-4" style={{ gridTemplateColumns: '1fr 1fr' }}>
                <div className="space-y-2">
                  <label htmlFor="password" className="label block">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      className="field-input pr-10"
                      placeholder="••••••••"
                      value={credentials.password}
                      onChange={handleChange}
                      disabled={isSubmitting}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1"
                      style={{ color: 'var(--muted)' }}
                      tabIndex={-1}
                    >
                      {showPassword ? <FiEyeOff size={18} /> : <FiEye size={18} />}
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <label htmlFor="confirmPassword" className="label block">
                    Confirm
                  </label>
                  <div className="relative">
                    <input
                      id="confirmPassword"
                      name="confirmPassword"
                      type={showConfirmPassword ? 'text' : 'password'}
                      className="field-input pr-10"
                      placeholder="••••••••"
                      value={credentials.confirmPassword}
                      onChange={handleChange}
                      disabled={isSubmitting}
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 p-1"
                      style={{ color: 'var(--muted)' }}
                      tabIndex={-1}
                    >
                      {showConfirmPassword ? <FiEyeOff size={18} /> : <FiEye size={18} />}
                    </button>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                className="btn btn-primary w-full text-center justify-center"
                disabled={
                  isSubmitting ||
                  !credentials.orgName.trim() ||
                  !credentials.email ||
                  !credentials.password ||
                  !credentials.confirmPassword
                }
              >
                {isSubmitting ? 'Creating account…' : 'Create Account'}
              </button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t" style={{ borderColor: 'var(--border)' }} />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2" style={{ background: 'var(--surface)', color: 'var(--muted)' }}>
                  or sign up with
                </span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleGoogleSignUp}
              className="btn btn-secondary w-full text-center justify-center"
              disabled={isSubmitting}
            >
              <SiGoogle size={16} />
              Google
            </button>

            <div className="text-center text-sm" style={{ color: 'var(--ink-2)' }}>
              Already have an account?{' '}
              <button
                type="button"
                onClick={() => navigate('/login')}
                className="font-semibold"
                style={{ color: 'var(--accent)', background: 'none', border: 'none', cursor: 'pointer' }}
              >
                Sign in
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
