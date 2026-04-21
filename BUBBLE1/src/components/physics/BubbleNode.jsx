import { useEffect, useId, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { usePhysicsWorld } from './PhysicsWorld'

export default function BubbleNode({
  label,
  onClick,
  radius = 58,
  to,
  initialPosition,
}) {
  const id = useId()
  const { registerBubble } = usePhysicsWorld()
  const bodyRef = useRef(null)
  const rafRef = useRef(0)
  const [position, setPosition] = useState(() => ({ x: -9999, y: -9999 }))

  const bubbleStyle = useMemo(() => {
    return {
      width: `${radius * 2}px`,
      height: `${radius * 2}px`,
      transform: `translate3d(${position.x - radius}px, ${position.y - radius}px, 0)`,
    }
  }, [position.x, position.y, radius])

  useEffect(() => {
    let disposed = false
    let unregister = null

    const loop = () => {
      if (bodyRef.current) {
        setPosition({
          x: bodyRef.current.position.x,
          y: bodyRef.current.position.y,
        })
      }
      rafRef.current = requestAnimationFrame(loop)
    }

    const tryRegister = () => {
      if (disposed) {
        return
      }

      const registration = registerBubble({
        id,
        radius,
        initialPosition,
      })

      if (!registration) {
        rafRef.current = requestAnimationFrame(tryRegister)
        return
      }

      bodyRef.current = registration.body
      unregister = registration.unregister
      rafRef.current = requestAnimationFrame(loop)
    }

    tryRegister()

    return () => {
      disposed = true
      cancelAnimationFrame(rafRef.current)
      if (unregister) {
        unregister()
      }
    }
  }, [id, initialPosition, radius, registerBubble])

  const commonClasses =
    'flex h-full w-full items-center justify-center rounded-full border border-[#FFF3C4] bg-[radial-gradient(circle_at_24%_24%,#FFF7DB,#EAAA00_40%,#BE8A00_100%)] px-3 text-center text-sm font-semibold uppercase tracking-[0.09em] text-[#002855] shadow-[0_14px_40px_rgba(0,0,0,0.32)] transition-transform duration-150 hover:scale-105 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#FFD46A]'

  return (
    <div className="pointer-events-none absolute left-0 top-0 z-20 will-change-transform" style={bubbleStyle}>
      {to ? (
        <Link to={to} className={`pointer-events-auto ${commonClasses}`} onClick={onClick}>
          {label}
        </Link>
      ) : (
        <button type="button" onClick={onClick} className={`pointer-events-auto ${commonClasses}`}>
          {label}
        </button>
      )}
    </div>
  )
}
