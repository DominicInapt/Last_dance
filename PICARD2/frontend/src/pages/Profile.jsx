import BubbleHeader from '../components/layout/BubbleHeader'

export default function Profile() {
  return (
    <BubbleHeader>
      <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 shadow-[0_18px_55px_rgba(0,0,0,0.45)]">
        <h1 className="text-3xl font-semibold text-amber-100">Profile</h1>
        <p className="mt-4 text-zinc-300">
          Manage your personal settings, visibility, and saved workflows.
        </p>
      </section>
    </BubbleHeader>
  )
}
