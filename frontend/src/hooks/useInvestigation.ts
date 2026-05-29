import { useContext } from 'react'
import { InvestigationContext, type InvestigationContextValue } from '../contexts/InvestigationContext'

export function useInvestigation(): InvestigationContextValue {
  const ctx = useContext(InvestigationContext)
  if (!ctx) throw new Error('useInvestigation must be used within InvestigationProvider')
  return ctx
}
