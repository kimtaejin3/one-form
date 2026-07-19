import type { ButtonHTMLAttributes } from 'react'

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'solid' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
}

export function Button({ variant = 'solid', size = 'md', className, ...props }: ButtonProps) {
  const classes = [
    'of-btn',
    variant === 'ghost' && 'of-btn--ghost',
    size !== 'md' && `of-btn--${size}`,
    className,
  ]
    .filter(Boolean)
    .join(' ')
  return <button className={classes} {...props} />
}
