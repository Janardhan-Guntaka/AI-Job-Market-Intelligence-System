import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Sidebar from './components/Sidebar'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import JobExplorer from './pages/JobExplorer'
import Analytics from './pages/Analytics'

const AppShell = ({ children }) => (
  <div className="flex min-h-screen">
    <Sidebar />
    <div className="flex-1 flex flex-col ml-64">
      <Navbar />
      <main className="flex-1 p-6 pt-24 animate-fade-in">
        {children}
      </main>
    </div>
  </div>
)

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<AppShell><Dashboard /></AppShell>} />
        <Route path="/jobs" element={<AppShell><JobExplorer /></AppShell>} />
        <Route path="/analytics" element={<AppShell><Analytics /></AppShell>} />
      </Routes>
    </BrowserRouter>
  )
}
