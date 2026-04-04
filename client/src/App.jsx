import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { GoogleOAuthProvider } from '@react-oauth/google'
import Sidebar from './components/Sidebar'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import JobExplorer from './pages/JobExplorer'
import Analytics from './pages/Analytics'
import Login from './pages/Login'

// A simple unprotected wrapper that ensures the user is logged in
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// Represents the authenticated application shell
const AppShell = ({ children }) => {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex-1 flex flex-col ml-64">
        <Navbar />
        <main className="flex-1 p-6 pt-24 animate-fade-in">
          {children}
        </main>
      </div>
    </div>
  );
};

export default function App() {
  // Use Vite env for Google Client ID (will default to a placeholder string if not set)
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com";

  return (
    <GoogleOAuthProvider clientId={clientId}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <AppShell><Dashboard /></AppShell>
            </ProtectedRoute>
          } />
          <Route path="/jobs" element={
            <ProtectedRoute>
              <AppShell><JobExplorer /></AppShell>
            </ProtectedRoute>
          } />
          <Route path="/analytics" element={
            <ProtectedRoute>
              <AppShell><Analytics /></AppShell>
            </ProtectedRoute>
          } />
        </Routes>
      </BrowserRouter>
    </GoogleOAuthProvider>
  )
}
