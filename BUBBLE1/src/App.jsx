import { Navigate, Route, Routes } from 'react-router-dom'
import Landing from './pages/Landing'
import Submit from './pages/Submit'
import Experiments from './pages/Experiments'
import Profile from './pages/Profile'
import About from './pages/About'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/about" element={<About />} />
      <Route path="/submit" element={<Submit />} />
      <Route path="/experiments" element={<Experiments />} />
      <Route path="/profile" element={<Profile />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
