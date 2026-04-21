import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'

export default function BubbleHeader({ children }) {
  return (
    <div className="relative min-h-screen bg-[radial-gradient(circle_at_top,rgba(255,212,106,0.18),transparent_36%),linear-gradient(158deg,#001F4D_0%,#002855_58%,#001737_100%)] text-zinc-100">
      <header className="fixed left-0 top-0 z-40 w-full">
        <div className="mx-auto flex max-w-6xl justify-center px-4 py-5 sm:justify-start">
          <motion.div
            initial={{ y: -10, opacity: 0 }}
            animate={{ y: [0, -5, 0], opacity: 1 }}
            transition={{ duration: 5.5, repeat: Infinity, ease: 'easeInOut' }}
          >
            <Link
              to="/"
              className="flex h-16 w-16 items-center justify-center rounded-full border border-[#FFF0B8] bg-[radial-gradient(circle_at_30%_30%,#FFF7DB,#EAAA00_46%,#C28A00)] text-sm font-bold uppercase tracking-[0.12em] text-[#002855] shadow-[0_12px_28px_rgba(0,0,0,0.35)]"
              aria-label="Return to landing page"
            >
              Picard
            </Link>
          </motion.div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-4 pb-12 pt-28">{children}</div>
    </div>
  )
}
