interface IntegrationCredentialFieldProps {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  configured: boolean
  hint?: string
  placeholder?: string
}

export default function IntegrationCredentialField({
  id,
  label,
  value,
  onChange,
  configured,
  hint,
  placeholder = 'Paste token here',
}: IntegrationCredentialFieldProps) {
  const isEditing = value.length > 0
  const showSaved = configured && !isEditing

  return (
    <div className="integration-field">
      <div className="integration-field-label-row">
        <label className="label block" htmlFor={id}>
          {label}
        </label>
        {configured ? (
          <span
            className={`integration-badge ${isEditing ? 'integration-badge--editing' : 'integration-badge--ok'}`}
          >
            {isEditing ? 'Replacing' : 'Saved'}
          </span>
        ) : (
          <span className="integration-badge integration-badge--missing">Not set</span>
        )}
      </div>
      {showSaved ? (
        <div className="integration-saved-value" aria-hidden="true">
          {hint || '••••••••••••••••'}
        </div>
      ) : null}
      <input
        id={id}
        className="field-input"
        type="password"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={showSaved ? 'Enter new token to replace' : placeholder}
        autoComplete="off"
      />
      {configured ? (
        <p className="integration-field-help">
          {isEditing
            ? 'New token will replace the saved one when you click Save.'
            : 'Token is stored securely. Leave blank to keep it, or type a new value to replace.'}
        </p>
      ) : (
        <p className="integration-field-help">Required for Coral to query this source.</p>
      )}
    </div>
  )
}
