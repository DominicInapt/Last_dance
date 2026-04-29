import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './lcars-assets/classic.css'
import './index.css'
import App from './App.jsx'
import { SoundProvider } from './components/audio/SoundProvider'
import { AuthProvider } from './components/auth/AuthProvider'
import { WorkspaceProvider } from './components/workspace/WorkspaceProvider'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <SoundProvider>
        <AuthProvider>
          <WorkspaceProvider>
            <App />
          </WorkspaceProvider>
        </AuthProvider>
      </SoundProvider>
    </BrowserRouter>
  </StrictMode>,
)
