import { createContext } from 'react'
import type { AuthContextValue } from '../types/context'

export const AuthContext = createContext<AuthContextValue | null>(null)
