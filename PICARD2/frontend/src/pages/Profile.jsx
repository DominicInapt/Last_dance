import BubbleHeader from '../components/layout/BubbleHeader'
import { useAuth } from '../components/auth/AuthProvider'

export default function Profile() {
  const { user } = useAuth()

  return (
    <BubbleHeader>
      <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-6 shadow-[0_18px_55px_rgba(0,0,0,0.45)]">
        <h1 className="text-3xl font-semibold text-amber-100">Profile</h1>
        <p className="mt-4 text-zinc-300">
          Signed in with GitHub as{' '}
          <span className="font-semibold text-amber-100">
            {user?.github_login || user?.username || 'unknown user'}
          </span>
          .
        </p>
        {user?.email ? (
          <p className="mt-3 text-zinc-300">Email: {user.email}</p>
        ) : null}
        {user?.profile_url ? (
          <a
            className="mt-4 inline-flex rounded-full border border-amber-200/40 px-4 py-2 text-sm font-medium text-amber-100 transition hover:border-amber-100 hover:text-white"
            href={user.profile_url}
            rel="noreferrer"
            target="_blank"
          >
            View GitHub profile
          </a>
        ) : null}
      </section>
    </BubbleHeader>
  )
}
