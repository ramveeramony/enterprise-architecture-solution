import React from 'react';
import { Outlet } from 'react-router-dom';

/**
 * Auth layout component for authentication pages
 */
const AuthLayout = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      <Outlet />
    </div>
  );
};

export default AuthLayout;