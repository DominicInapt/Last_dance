const STATUS_VARIANTS = {
  Pending: 'status-badge pending',
  Queued: 'status-badge queued',
  Running: 'status-badge running',
  Success: 'status-badge success',
  Failed: 'status-badge failed',
}

export default function StatusBadge({ status }) {
  const className = STATUS_VARIANTS[status] || 'status-badge neutral'
  return <span className={className}>{status || 'Unknown'}</span>
}