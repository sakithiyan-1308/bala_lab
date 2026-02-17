import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNavigate } from 'react-router-dom';
import { Button, Input, Card } from '../components/ui';
import { toast } from 'sonner';

export const AuthPage = ({ mode = 'login' }) => {
  const [isLogin, setIsLogin] = useState(mode === 'login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('user');
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register(email, password, role);
      }
      toast.success(isLogin ? 'Logged in successfully' : 'Registered successfully');
      navigate('/');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Authentication failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-md p-8 bg-white">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-heading font-bold text-slate-900">Bala Lab</h1>
          <p className="text-slate-600 mt-2">{isLogin ? 'Sign in to your account' : 'Create a new account'}</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Email</label>
            <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="name@example.com" />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Password</label>
            <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="••••••••" />
          </div>
          
          {!isLogin && (
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Role</label>
              <select 
                value={role} 
                onChange={(e) => setRole(e.target.value)}
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              >
                <option value="user">Patient / User</option>
                <option value="admin">Lab Administrator</option>
              </select>
            </div>
          )}

          <Button type="submit" className="w-full mt-6">
            {isLogin ? 'Sign In' : 'Register'}
          </Button>
        </form>

        <div className="mt-6 text-center">
          <button 
            onClick={() => setIsLogin(!isLogin)}
            className="text-sm text-accent hover:underline font-medium"
          >
            {isLogin ? "Don't have an account? Register" : 'Already have an account? Sign In'}
          </button>
        </div>
      </Card>
    </div>
  );
};
