import { GoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Briefcase, Database } from 'lucide-react';
import { useState } from 'react';
import axios from 'axios';

export default function Login() {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSuccess = async (credentialResponse) => {
    setLoading(true);
    setError('');
    try {
      // Send the token to our backend to verify and issue an app token
      const res = await axios.post('/api/auth/google', {
        credential: credentialResponse.credential
      });
      
      const { access_token, user } = res.data;
      
      // Store token
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      // Redirect to dashboard
      window.location.href = '/dashboard';
    } catch (err) {
      console.error('Authentication failed:', err);
      setError('Failed to authenticate with the server.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden" 
         style={{ background: '#020813' }}>
      
      {/* Background decorations */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-3xl" />
      <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl" />

      <div className="z-10 w-full max-w-md p-8">
        <div className="glass-card p-10 flex flex-col items-center text-center">
          
          <div className="w-16 h-16 rounded-2xl mb-6 flex items-center justify-center border border-white/10 shadow-2xl"
               style={{ background: 'linear-gradient(135deg, #2563eb, #7c3aed)' }}>
            <Sparkles className="w-8 h-8 text-white" />
          </div>

          <h1 className="text-3xl font-bold text-white mb-2">
            AI Job <span className="gradient-text">Intel</span>
          </h1>
          <p className="text-slate-400 text-sm mb-8">
            Sign in to access real-time market intelligence and analytics.
          </p>

          <div className="space-y-4 w-full">
            <div className="flex items-center justify-center p-4 rounded-xl bg-surface-700/50 border border-white/5 mx-auto">
                <GoogleLogin
                  onSuccess={handleSuccess}
                  onError={() => setError('Google Login Failed')}
                  theme="filled_black"
                  shape="circle"
                  size="large"
                  text="continue_with"
                  width="100%"
                />
            </div>
          </div>

          {loading && (
            <div className="mt-4 text-xs text-brand-400 animate-pulse">
              Authenticating...
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500 text-xs">
              {error}
            </div>
          )}

          <div className="mt-10 grid grid-cols-2 gap-4 text-left w-full border-t border-white/5 pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-surface-600"><Database className="w-4 h-4 text-brand-400" /></div>
              <span className="text-xs text-slate-300 font-medium">Real-time Data</span>
            </div>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-surface-600"><Briefcase className="w-4 h-4 text-purple-400" /></div>
              <span className="text-xs text-slate-300 font-medium">Smart Insights</span>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
