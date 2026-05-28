export interface AlertProps {
  message: string
  type: 'error' | 'warning' | 'success' | 'info'
  dismissible?: boolean
  onDismiss?: () => void
}

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  onClick?: () => void
  children: React.ReactNode
}

export interface FormFieldProps {
  label: string
  error?: string
  required?: boolean
  hint?: string
}

export interface CardProps {
  title?: string
  description?: string
  children: React.ReactNode
  className?: string
}

export interface PaginationState {
  page: number
  pageSize: number
  total: number
}

export interface LoadingState {
  isLoading: boolean
  error: string | null
  data: unknown | null
}
