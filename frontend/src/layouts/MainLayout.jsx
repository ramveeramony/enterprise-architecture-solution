import React, { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { Sidebar, Navbar, Avatar, Dropdown } from 'flowbite-react';
import { 
  FiHome, 
  FiLayers, 
  FiDatabase, 
  FiPackage, 
  FiSettings, 
  FiMenu, 
  FiX, 
  FiUser,
  FiLogOut,
  FiCpu
} from 'react-icons/fi';

import { useAuth } from '../services/auth';

/**
 * Main layout component with sidebar navigation and header
 */
const MainLayout = () => {
  const location = useLocation();
  const { logout, user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };
  
  const closeSidebar = () => {
    if (window.innerWidth < 1024) {
      setSidebarOpen(false);
    }
  };
  
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-10 bg-black bg-opacity-50 lg:hidden"
          onClick={toggleSidebar}
        />
      )}
      
      {/* Sidebar */}
      <div 
        className={`fixed inset-y-0 left-0 z-20 w-64 transform bg-white transition duration-200 ease-in-out lg:static lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-full flex-col">
          <div className="flex items-center justify-between border-b p-4">
            <Link to="/">
              <span className="text-xl font-semibold text-blue-600">EA Solution</span>
            </Link>
            <button 
              className="rounded-md p-2 text-gray-500 hover:bg-gray-100 lg:hidden"
              onClick={toggleSidebar}
            >
              <FiX className="h-6 w-6" />
            </button>
          </div>
          
          <Sidebar className="h-full w-full border-r border-gray-200">
            <Sidebar.Items>
              <Sidebar.ItemGroup>
                <Sidebar.Item
                  as={Link}
                  to="/"
                  icon={FiHome}
                  active={location.pathname === '/'}
                  onClick={closeSidebar}
                >
                  Dashboard
                </Sidebar.Item>
                <Sidebar.Item
                  as={Link}
                  to="/modeling"
                  icon={FiLayers}
                  active={location.pathname === '/modeling'}
                  onClick={closeSidebar}
                >
                  Modeling
                </Sidebar.Item>
                <Sidebar.Item
                  as={Link}
                  to="/repository"
                  icon={FiDatabase}
                  active={location.pathname === '/repository'}
                  onClick={closeSidebar}
                >
                  Repository
                </Sidebar.Item>
                <Sidebar.Item
                  as={Link}
                  to="/integration"
                  icon={FiPackage}
                  active={location.pathname === '/integration'}
                  onClick={closeSidebar}
                >
                  Integrations
                </Sidebar.Item>
                <Sidebar.Item
                  as={Link}
                  to="/genai"
                  icon={FiCpu}
                  active={location.pathname === '/genai'}
                  onClick={closeSidebar}
                >
                  GenAI Features
                </Sidebar.Item>
                <Sidebar.Item
                  as={Link}
                  to="/settings"
                  icon={FiSettings}
                  active={location.pathname === '/settings'}
                  onClick={closeSidebar}
                >
                  Settings
                </Sidebar.Item>
              </Sidebar.ItemGroup>
            </Sidebar.Items>
          </Sidebar>
        </div>
      </div>
      
      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <Navbar className="border-b border-gray-200 bg-white px-4">
          <div className="flex w-full items-center justify-between">
            <button 
              className="rounded-md p-2 text-gray-500 hover:bg-gray-100 lg:hidden"
              onClick={toggleSidebar}
            >
              <FiMenu className="h-6 w-6" />
            </button>
            
            <div className="flex items-center space-x-4">
              <Dropdown
                label={<Avatar rounded alt="User" />}
                arrowIcon={false}
                inline
              >
                <Dropdown.Header>
                  <span className="block text-sm">{user?.name || 'User'}</span>
                  <span className="block truncate text-sm font-medium">{user?.email || 'user@example.com'}</span>
                </Dropdown.Header>
                <Dropdown.Item icon={FiUser}>
                  Profile
                </Dropdown.Item>
                <Dropdown.Divider />
                <Dropdown.Item icon={FiLogOut} onClick={logout}>
                  Sign out
                </Dropdown.Item>
              </Dropdown>
            </div>
          </div>
        </Navbar>
        
        {/* Page content */}
        <div className="flex-1 overflow-auto">
          <Outlet />
        </div>
      </div>
    </div>
  );
};

export default MainLayout;