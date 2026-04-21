import { useMemo } from 'react'
import BubbleNode from '../components/physics/BubbleNode'
import { PhysicsWorld } from '../components/physics/PhysicsWorld'
import { useAuth } from '../components/auth/AuthProvider'

function centerSpawn(index, total) {
  const width = window.innerWidth || 1200
  const height = window.innerHeight || 800
  const angle = (Math.PI * 2 * index) / Math.max(1, total)
  const distance = 60 + Math.random() * 90

  return {
    x: width / 2 + Math.cos(angle) * distance,
    y: height / 2 + Math.sin(angle) * distance,
  }
}

export default function Landing() {
  const { isAuthenticated, login, logout } = useAuth()

  const bubbles = useMemo(() => {
    const publicNodes = [
      { label: 'About', to: '/about', radius: 58 },
      { label: 'Login', onClick: login, radius: 62 },
    ]

    if (!isAuthenticated) {
      return publicNodes
    }

    return [
      { label: 'About', to: '/about', radius: 56 },
      { label: 'Logout', onClick: logout, radius: 58 },
      { label: 'Experiments', to: '/experiments', radius: 68 },
      { label: 'Submit', to: '/submit', radius: 60 },
      { label: 'Profile', to: '/profile', radius: 58 },
    ]
  }, [isAuthenticated, login, logout])

  return (
    <main className="h-screen w-full bg-transparent text-zinc-100">
      <PhysicsWorld className="h-full w-full bg-transparent">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(234,170,0,0.2),rgba(0,0,0,0)_46%)]" />
        {bubbles.map((bubble, index) => (
          <BubbleNode
            key={bubble.label}
            label={bubble.label}
            onClick={bubble.onClick}
            to={bubble.to}
            radius={bubble.radius}
            initialPosition={centerSpawn(index, bubbles.length)}
          />
        ))}
      </PhysicsWorld>
    </main>
  )
}
