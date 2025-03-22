import React, { useEffect, useState } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Flowbite } from 'flowbite-react';

// Layout components
import MainLayout from './layouts/MainLayout';
import AuthLayout from './layouts/AuthLayout';

// Pages
import Dashboard from './pages/Dashboard';
import Modeling from './pages/Modeling';
import Repository from './pages/Repository';
import Integration from './pages/Integration';
import Settings from './pages/Settings';
import GenAIPage from './pages/GenAIPage';
import Login from './pages/Login';
import NotFound from './pages/NotFound';

// Authentication service
import { useAuth } from './services/auth';

// Theme configuration
import { theme } from './theme';

const App = () => {
  const { isAuthenticated, loading, initAuth } = useAuth();
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    // Initialize authentication
    initAuth().then(() => {
      setInitialized(true);
    });
  }, [initAuth]);

  if (!initialized || loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-blue-600 border-t-transparent mx-auto"></div>
          <p className="text-gray-700">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <Flowbite theme={{ theme }}>
      <Routes>
        {/* Public routes */}
        <Route element={<AuthLayout />}>
          <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/" />} />
        </Route>

        {/* Protected routes */}
        <Route element={<MainLayout />}>
          <Route path="/" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
          <Route path="/modeling" element={isAuthenticated ? <Modeling /> : <Navigate to="/login" />} />
          <Route path="/repository" element={isAuthenticated ? <Repository /> : <Navigate to="/login" />} />
          <Route path="/integration" element={isAuthenticated ? <Integration /> : <Navigate to="/login" />} />
          <Route path="/genai" element={isAuthenticated ? <GenAIPage /> : <Navigate to="/login" />} />
          <Route path="/settings" element={isAuthenticated ? <Settings /> : <Navigate to="/login" />} />
        </Route>

        {/* 404 route */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Flowbite>
  );
};

export default App;