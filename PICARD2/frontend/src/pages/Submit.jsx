import BubbleHeader from '../components/layout/BubbleHeader'
import BubbleNode from '../components/physics/BubbleNode'
import { PhysicsWorld } from '../components/physics/PhysicsWorld'

export default function Submit() {
  return (
    <BubbleHeader>
      <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 shadow-[0_18px_55px_rgba(0,0,0,0.45)]">
        <h1 className="text-3xl font-semibold text-amber-100">Submit Work</h1>
        <p className="mt-4 max-w-3xl text-zinc-300">
          Upload source code, datasets, or experiment metadata with clear naming and
          reproducible instructions. Include a short README in each submission bundle
          describing required dependencies and expected outputs.
        </p>
      </section>

      <section className="mt-8 h-[60vh] min-h-[380px] overflow-hidden rounded-3xl border border-white/10 bg-black/40">
        <PhysicsWorld className="h-full w-full">
          <BubbleNode label="Submit Algorithm" radius={76} initialPosition={{ x: 360, y: 180 }} />
          <BubbleNode label="Submit Dataset" radius={76} initialPosition={{ x: 560, y: 210 }} />
          <BubbleNode label="Submit Experiment" radius={86} initialPosition={{ x: 480, y: 320 }} />
        </PhysicsWorld>
      </section>
    </BubbleHeader>
  )
}
