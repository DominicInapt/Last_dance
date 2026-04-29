import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react'
import beep1 from '../../lcars-assets/beep1.mp3'
import beep2 from '../../lcars-assets/beep2.mp3'
import beep3 from '../../lcars-assets/beep3.mp3'
import beep4 from '../../lcars-assets/beep4.mp3'

const STORAGE_KEY = 'picard.lcars.sound'
const SoundContext = createContext(null)

export function SoundProvider({ children }) {
  const soundsRef = useRef({})
  const [soundEnabled, setSoundEnabled] = useState(true)

  useEffect(() => {
    const storedValue = window.localStorage.getItem(STORAGE_KEY)
    if (storedValue !== null) {
      setSoundEnabled(storedValue !== 'false')
    }
  }, [])

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, soundEnabled ? 'true' : 'false')
  }, [soundEnabled])

  useEffect(() => {
    const sounds = {
      confirm: new Audio(beep1),
      nav: new Audio(beep2),
      soft: new Audio(beep3),
      alert: new Audio(beep4),
    }

    Object.values(sounds).forEach((sound) => {
      sound.preload = 'auto'
    })

    soundsRef.current = sounds

    return () => {
      Object.values(soundsRef.current).forEach((sound) => {
        sound.pause()
      })
      soundsRef.current = {}
    }
  }, [])

  function play(name = 'nav') {
    if (!soundEnabled) {
      return Promise.resolve()
    }

    const sound = soundsRef.current[name] || soundsRef.current.nav
    if (!sound) {
      return Promise.resolve()
    }

    sound.pause()
    sound.currentTime = 0
    return sound.play().catch(() => undefined)
  }

  const value = useMemo(() => {
    return {
      soundEnabled,
      toggleSound: () => setSoundEnabled((current) => !current),
      play,
    }
  }, [soundEnabled])

  return <SoundContext.Provider value={value}>{children}</SoundContext.Provider>
}

export function useSound() {
  const context = useContext(SoundContext)
  if (!context) {
    throw new Error('useSound must be used inside SoundProvider')
  }
  return context
}