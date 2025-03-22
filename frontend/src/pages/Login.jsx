import React, { useState } from 'react';
import { Card, Button, Label, TextInput, Alert } from 'flowbite-react';
import { FiMail, FiLock, FiAlertCircle, FiLogIn } from 'react-icons/fi';

import { useAuth } from '../services/auth';

/**
 * Login page component
 */
const Login = () => {
  const { loginWithEmailPassword, loginWithEntraId, loading } = useAuth();
  const [form, setForm] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState(null);
  
  const handleChange = (e) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    
    try {
      await loginWithEmailPassword(form.email, form.password);
    } catch (error) {
      setError(error.message || 'Failed to login');
    }
  };
  
  const handleEntraLogin = async () => {
    setError(null);
    
    try {
      await loginWithEntraId();
    } catch (error) {
      setError(error.message || 'Failed to login with Microsoft Entra ID');
    }
  };
  
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 p-4">
      <Card className="w-full max-w-md">
        <div className="mb-4 flex justify-center">
          <div className="h-16 w-16 rounded-full bg-blue-600 p-4">
            <FiLogIn className="h-full w-full text-white" />
          </div>
        </div>
        
        <h2 className="mb-2 text-center text-2xl font-bold text-gray-900">
          Enterprise Architecture Solution
        </h2>
        <p className="mb-4 text-center text-gray-600">
          Sign in to your account
        </p>
        
        {error && (
          <Alert color="failure" className="mb-4">
            <div className="flex items-center gap-2">
              <FiAlertCircle className="h-4 w-4" />
              <span>{error}</span>
            </div>
          </Alert>
        )}
        
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <div className="mb-2 block">
              <Label htmlFor="email" value="Email" />
            </div>
            <TextInput
              id="email"
              name="email"
              placeholder="name@example.com"
              value={form.email}
              onChange={handleChange}
              icon={FiMail}
              required
            />
          </div>
          
          <div>
            <div className="mb-2 block">
              <Label htmlFor="password" value="Password" />
            </div>
            <TextInput
              id="password"
              name="password"
              type="password"
              placeholder="••••••••"
              value={form.password}
              onChange={handleChange}
              icon={FiLock}
              required
            />
          </div>
          
          <Button 
            type="submit" 
            color="blue"
            disabled={loading}
            isProcessing={loading}
          >
            Sign in
          </Button>
        </form>
        
        <div className="my-4 flex items-center">
          <div className="flex-grow border-t border-gray-300"></div>
          <div className="px-4 text-center text-sm text-gray-500">OR</div>
          <div className="flex-grow border-t border-gray-300"></div>
        </div>
        
        <Button 
          color="light" 
          onClick={handleEntraLogin}
          disabled={loading}
          isProcessing={loading}
        >
          <svg className="mr-2 h-5 w-5" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20.25 10.5C20.25 4.95 15.6 0.375 10.125 0.375C4.575 0.375 0 4.95 0 10.5C0 15.6 3.825 19.8 8.775 20.55V13.5H6.375V10.5H8.775V8.025C8.775 5.7 10.275 4.35 12.375 4.35C13.5 4.35 14.55 4.575 14.55 4.575V6.9H13.275C12.075 6.9 11.625 7.725 11.625 8.625V10.5H14.4L13.95 13.5H11.625V20.55C16.575 19.8 20.25 15.6 20.25 10.5Z" fill="#1877F2"/>
          </svg>
          Sign in with Microsoft Entra ID
        </Button>
      </Card>
    </div>
  );
};

export default Login;