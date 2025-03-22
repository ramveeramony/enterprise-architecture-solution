import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Navbar, Sidebar, Footer } from '../components/layout';
import { useAuth } from '../services/auth';

const MainLayout = () => {
  const { user } = useAuth();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <Sidebar collapsed={sidebarCollapsed} user={user} />

      {/* Main Content */}
      <div className="flex flex-col flex-1 w-full">
        <Navbar onMenuClick={toggleSidebar} user={user} />
        
        <main className="h-full overflow-y-auto">
          <div className="container mx-auto">
            <Outlet />
          </div>
        </main>

        <Footer />
      </div>
    </div>
  );
};

export default MainLayout;