import { Navigate, Route, Routes } from 'react-router-dom'
import Landing from './pages/Landing'
import Submit from './pages/Submit'
import Experiments from './pages/Experiments'
import Profile from './pages/Profile'
import About from './pages/About'
import { useAuth } from './components/auth/AuthProvider'

function RequireAuth({ children }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return null
  }

  if (!isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return children
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/about" element={<About />} />
      <Route
        path="/submit"
        element={
          <RequireAuth>
            <Submit />
          </RequireAuth>
        }
      />
      <Route
        path="/experiments"
        element={
          <RequireAuth>
            <Experiments />
          </RequireAuth>
        }
      />
      <Route
        path="/profile"
        element={
          <RequireAuth>
            <Profile />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
