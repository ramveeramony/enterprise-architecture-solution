import React, { useState } from 'react';
import { Button, Checkbox, Label, TextInput, Alert } from 'flowbite-react';
import { FiMail, FiLock, FiAlertCircle, FiArrowRight } from 'react-icons/fi';
import { useAuth } from '../services/auth';

const Login = () => {
  const { login, loginWithMicrosoft } = useAuth();
  const [loginData, setLoginData] = useState({
    email: '',
    password: '',
    rememberMe: false,
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showRegister, setShowRegister] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setLoginData({
      ...loginData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const result = await login(loginData.email, loginData.password);
      if (!result.success) {
        setError(result.error || 'Login failed. Please check your credentials.');
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleMicrosoftLogin = async () => {
    setError('');
    setLoading(true);

    try {
      const result = await loginWithMicrosoft();
      if (!result.success) {
        setError(result.error || 'Microsoft login failed. Please try again.');
      }
    } catch (err) {
      setError('An unexpected error occurred. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 text-center">
        Sign in to your account
      </h2>

      {error && (
        <Alert color="failure" icon={FiAlertCircle} className="mb-4">
          <span className="font-medium">Error!</span> {error}
        </Alert>
      )}

      <form className="space-y-4" onSubmit={handleSubmit}>
        <div>
          <Label htmlFor="email" value="Email" />
          <TextInput
            id="email"
            name="email"
            type="email"
            placeholder="name@company.com"
            required
            icon={FiMail}
            value={loginData.email}
            onChange={handleChange}
          />
        </div>
        <div>
          <Label htmlFor="password" value="Password" />
          <TextInput
            id="password"
            name="password"
            type="password"
            placeholder="••••••••"
            required
            icon={FiLock}
            value={loginData.password}
            onChange={handleChange}
          />
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Checkbox
              id="rememberMe"
              name="rememberMe"
              checked={loginData.rememberMe}
              onChange={handleChange}
            />
            <Label htmlFor="rememberMe">Remember me</Label>
          </div>
          <a
            href="#"
            className="text-sm text-blue-700 hover:underline dark:text-blue-500"
          >
            Forgot password?
          </a>
        </div>
        <Button
          type="submit"
          className="w-full"
          gradientDuoTone="purpleToBlue"
          disabled={loading}
        >
          {loading ? 'Signing in...' : 'Sign in'}
        </Button>

        <div className="flex items-center justify-center">
          <hr className="w-full border-gray-300" />
          <span className="px-3 text-gray-500 text-sm">or</span>
          <hr className="w-full border-gray-300" />
        </div>

        <Button
          type="button"
          color="light"
          className="w-full"
          onClick={handleMicrosoftLogin}
          disabled={loading}
        >
          <img
            src="/microsoft-logo.svg"
            alt="Microsoft logo"
            className="w-5 h-5 mr-2"
          />
          Sign in with Microsoft
        </Button>

        <div className="text-sm font-medium text-gray-500 dark:text-gray-400 text-center">
          Don't have an account?{' '}
          <a
            href="#"
            className="text-blue-700 hover:underline dark:text-blue-500"
            onClick={(e) => {
              e.preventDefault();
              setShowRegister(true);
            }}
          >
            Create account
          </a>
        </div>
      </form>
    </div>
  );
};

export default Login;