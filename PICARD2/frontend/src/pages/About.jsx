import BubbleHeader from '../components/layout/BubbleHeader'

export default function About() {
  return (
    <BubbleHeader>
      <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 shadow-[0_18px_55px_rgba(0,0,0,0.45)]">
        <h1 className="text-3xl font-semibold text-amber-100">About Picard</h1>
        <p className="mt-4 max-w-3xl text-zinc-300">
          Picard is an exploratory interface where navigation and interaction are modeled
          as kinetic objects. Bubbles embody app sections and collide to create a dynamic
          spatial map of your workflow.
        </p>
      </section>
    </BubbleHeader>
  )
}
