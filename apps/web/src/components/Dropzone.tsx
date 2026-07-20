import { Icon } from './Icon'

type Props = {
  title: string
  desc: string
  accept: string
  buttonLabel: string
  busy?: boolean
  busyLabel?: string
  onFile: () => void
}

export default function Dropzone({ title, desc, accept, buttonLabel, busy, busyLabel, onFile }: Props) {
  return (
    <label className="dropzone">
      <input type="file" hidden accept={accept} onChange={onFile} disabled={busy} />
      <span className="dropzone-icon">
        <Icon name="upload" size={26} />
      </span>
      <strong className="dropzone-title">{title}</strong>
      <span className="dropzone-desc">{desc}</span>
      <span className="of-btn of-btn--sm">{busy ? busyLabel : buttonLabel}</span>
    </label>
  )
}
