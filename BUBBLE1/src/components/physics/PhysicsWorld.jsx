import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'react'
import Matter from 'matter-js'

const PhysicsWorldContext = createContext(null)

function makeWalls(width, height) {
  const thickness = 100
  const opts = {
    isStatic: true,
    restitution: 1.04,
    friction: 0,
    frictionStatic: 0,
  }

  return [
    Matter.Bodies.rectangle(width / 2, -thickness / 2, width, thickness, opts),
    Matter.Bodies.rectangle(
      width / 2,
      height + thickness / 2,
      width,
      thickness,
      opts,
    ),
    Matter.Bodies.rectangle(-thickness / 2, height / 2, thickness, height, opts),
    Matter.Bodies.rectangle(
      width + thickness / 2,
      height / 2,
      thickness,
      height,
      opts,
    ),
  ]
}

export function PhysicsWorld({
  children,
  className = '',
  style,
}) {
  const BASE_MAX_BUBBLE_SPEED = 24
  const containerRef = useRef(null)
  const engineRef = useRef(null)
  const runnerRef = useRef(null)
  const wallsRef = useRef([])
  const bubblesRef = useRef(new Map())
  const runningRef = useRef(false)
  const velocityScaleRef = useRef(1)

  const [velocityScale, setVelocityScale] = useState(1)

  useEffect(() => {
    velocityScaleRef.current = velocityScale
  }, [velocityScale])

  const clampBodySpeed = useCallback((body) => {
    const maxBubbleSpeed = BASE_MAX_BUBBLE_SPEED * velocityScaleRef.current
    const speed = body.speed
    if (speed <= maxBubbleSpeed || speed === 0) {
      return
    }

    const scale = maxBubbleSpeed / speed
    Matter.Body.setVelocity(body, {
      x: body.velocity.x * scale,
      y: body.velocity.y * scale,
    })
  }, [BASE_MAX_BUBBLE_SPEED])

  const startRunner = useCallback(() => {
    if (!engineRef.current || !runnerRef.current || runningRef.current) {
      return
    }
    Matter.Runner.run(runnerRef.current, engineRef.current)
    runningRef.current = true
  }, [])

  const stopRunner = useCallback(() => {
    if (!runnerRef.current || !runningRef.current) {
      return
    }
    Matter.Runner.stop(runnerRef.current)
    runningRef.current = false
  }, [])

  const syncBounds = useCallback(() => {
    if (!containerRef.current || !engineRef.current) {
      return
    }

    const rect = containerRef.current.getBoundingClientRect()
    const width = Math.max(320, Math.floor(rect.width))
    const height = Math.max(240, Math.floor(rect.height))

    if (wallsRef.current.length > 0) {
      Matter.World.remove(engineRef.current.world, wallsRef.current)
    }

    wallsRef.current = makeWalls(width, height)
    Matter.World.add(engineRef.current.world, wallsRef.current)
  }, [])

  useEffect(() => {
    const engine = Matter.Engine.create({
      gravity: { x: 0, y: 0 },
    })

    // Increase solver quality to keep collisions stable as speeds grow over time.
    engine.positionIterations = 10
    engine.velocityIterations = 8
    engine.constraintIterations = 4

    const runner = Matter.Runner.create()
    engineRef.current = engine
    runnerRef.current = runner

    const accelerateBodies = () => {
      if (!containerRef.current) {
        return
      }

      const rect = containerRef.current.getBoundingClientRect()
      const width = Math.max(320, Math.floor(rect.width))
      const height = Math.max(240, Math.floor(rect.height))

      for (const { body, acceleration } of bubblesRef.current.values()) {
        const scale = velocityScaleRef.current

        Matter.Body.applyForce(body, body.position, {
          x: body.mass * acceleration.x * scale,
          y: body.mass * acceleration.y * scale,
        })

        const cornerMargin = body.circleRadius + 16
        const nearLeft = body.position.x < cornerMargin
        const nearRight = body.position.x > width - cornerMargin
        const nearTop = body.position.y < cornerMargin
        const nearBottom = body.position.y > height - cornerMargin

        const trappedInCorner = (nearLeft || nearRight) && (nearTop || nearBottom)
        if (trappedInCorner) {
          const toCenterX = width / 2 - body.position.x
          const toCenterY = height / 2 - body.position.y
          const length = Math.hypot(toCenterX, toCenterY) || 1

          Matter.Body.applyForce(body, body.position, {
            x: body.mass * (toCenterX / length) * (0.028 * scale),
            y: body.mass * (toCenterY / length) * (0.028 * scale),
          })

          Matter.Body.setVelocity(body, {
            x: body.velocity.x + (toCenterX / length) * (10 * scale),
            y: body.velocity.y + (toCenterY / length) * (10 * scale),
          })
        } else if (body.speed < 6.5 * scale) {
          // Keep bubbles from stalling after low-energy impacts.
          const randomAngle = Math.random() * Math.PI * 2
          Matter.Body.setVelocity(body, {
            x: body.velocity.x + Math.cos(randomAngle) * (3 * scale),
            y: body.velocity.y + Math.sin(randomAngle) * (3 * scale),
          })
        }

        clampBodySpeed(body)
      }
    }

    const boostCollisions = (event) => {
      for (const pair of event.pairs) {
        const bodies = [pair.bodyA, pair.bodyB]

        for (const body of bodies) {
          if (body.isStatic) {
            continue
          }

          const energyScale = 1.06 + 0.08 * velocityScaleRef.current
          Matter.Body.setVelocity(body, {
            x: body.velocity.x * energyScale,
            y: body.velocity.y * energyScale,
          })

          clampBodySpeed(body)
        }
      }
    }

    Matter.Events.on(engine, 'beforeUpdate', accelerateBodies)
    Matter.Events.on(engine, 'collisionStart', boostCollisions)

    syncBounds()
    startRunner()

    const resizeObserver = new ResizeObserver(() => {
      syncBounds()
    })

    if (containerRef.current) {
      resizeObserver.observe(containerRef.current)
    }

    window.addEventListener('resize', syncBounds)

    return () => {
      window.removeEventListener('resize', syncBounds)
      resizeObserver.disconnect()
      stopRunner()
      Matter.Events.off(engine, 'beforeUpdate', accelerateBodies)
      Matter.Events.off(engine, 'collisionStart', boostCollisions)

      Matter.World.clear(engine.world, false)
      Matter.Engine.clear(engine)

      bubblesRef.current.clear()
      wallsRef.current = []
      engineRef.current = null
      runnerRef.current = null
    }
  }, [clampBodySpeed, startRunner, stopRunner, syncBounds])

  const registerBubble = useCallback(({ id, radius, initialPosition }) => {
    if (!engineRef.current || !containerRef.current) {
      return null
    }

    const rect = containerRef.current.getBoundingClientRect()
    const width = Math.max(320, Math.floor(rect.width))
    const height = Math.max(240, Math.floor(rect.height))

    const centerX = width / 2
    const centerY = height / 2

    const body = Matter.Bodies.circle(
      initialPosition?.x ?? centerX + (Math.random() - 0.5) * 120,
      initialPosition?.y ?? centerY + (Math.random() - 0.5) * 120,
      radius,
      {
        restitution: 1.02,
        friction: 0.001,
        frictionAir: 0,
        density: 0.001,
      },
    )

    const angle = Math.random() * Math.PI * 2
    const accelerationMagnitude = 0.00024
    const acceleration = {
      x: Math.cos(angle) * accelerationMagnitude,
      y: Math.sin(angle) * accelerationMagnitude,
    }

    Matter.World.add(engineRef.current.world, body)
    bubblesRef.current.set(id, { body, radius, acceleration })

    const scale = velocityScaleRef.current

    Matter.Body.setVelocity(body, {
      x: (Math.random() - 0.5) * (14 * scale),
      y: (Math.random() - 0.5) * (14 * scale),
    })

    Matter.Body.applyForce(body, body.position, {
      x: (Math.random() - 0.5) * (0.026 * scale),
      y: (Math.random() - 0.5) * (0.026 * scale),
    })

    return {
      body,
      unregister: () => {
        if (!engineRef.current) {
          return
        }
        Matter.World.remove(engineRef.current.world, body)
        bubblesRef.current.delete(id)
      },
    }
  }, [])

  const value = useMemo(() => {
    return { registerBubble }
  }, [registerBubble])

  return (
    <PhysicsWorldContext.Provider value={value}>
      <div ref={containerRef} className={`relative overflow-hidden ${className}`} style={style}>
        <div className="absolute bottom-4 left-4 z-30 w-64 rounded-xl border border-white/25 bg-[#001737cc] p-3 text-zinc-100 backdrop-blur">
          <label htmlFor="velocity-slider" className="mb-2 block text-xs font-semibold uppercase tracking-[0.12em]">
            Bubble Velocity
          </label>
          <input
            id="velocity-slider"
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={velocityScale}
            onChange={(event) => setVelocityScale(Number(event.target.value))}
            className="h-2 w-full cursor-pointer accent-[#EAAA00]"
          />
          <p className="mt-2 text-xs text-zinc-300">Speed: {velocityScale.toFixed(2)}x</p>
        </div>
        {children}
      </div>
    </PhysicsWorldContext.Provider>
  )
}

export function usePhysicsWorld() {
  const ctx = useContext(PhysicsWorldContext)
  if (!ctx) {
    throw new Error('usePhysicsWorld must be used inside PhysicsWorld')
  }
  return ctx
}
