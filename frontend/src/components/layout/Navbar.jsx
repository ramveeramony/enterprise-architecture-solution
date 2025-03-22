import React from 'react';
import { Avatar, Dropdown, Button } from 'flowbite-react';
import { Link } from 'react-router-dom';
import { FiMenu, FiBell, FiSettings, FiLogOut, FiUser } from 'react-icons/fi';
import { useAuth } from '../../services/auth';

const Navbar = ({ onMenuClick, user }) => {
  const { logout } = useAuth();

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-sm z-30">
      <div className="px-3 py-3 lg:px-5 lg:pl-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={onMenuClick}
              aria-label="Toggle Menu"
              className="p-2 rounded-md lg:hidden text-gray-600 hover:text-gray-900 hover:bg-gray-100 focus:outline-none focus:bg-gray-100 focus:text-gray-900"
            >
              <FiMenu className="h-6 w-6" />
            </button>
            <div className="hidden lg:block ml-4">
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                Enterprise Architecture Solution
              </h1>
            </div>
          </div>

          <div className="flex items-center">
            {/* Search */}
            <div className="relative mr-4 lg:mr-6">
              <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <svg className="h-5 w-5 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <input
                className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-gray-50 placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50 sm:text-sm"
                type="search"
                placeholder="Search..."
              />
            </div>

            {/* Notifications */}
            <Button color="gray" className="mr-2 p-2">
              <FiBell className="h-5 w-5" />
              <span className="sr-only">Notifications</span>
            </Button>

            {/* User Menu */}
            <Dropdown
              arrowIcon={false}
              inline
              label={
                <Avatar
                  alt="User"
                  img="https://i.pravatar.cc/150?img=12"
                  rounded
                  size="sm"
                  className="ring-2 ring-blue-500"
                />
              }
            >
              <Dropdown.Header>
                <span className="block text-sm font-medium">{user?.name || 'User'}</span>
                <span className="block truncate text-sm">{user?.email || 'user@example.com'}</span>
              </Dropdown.Header>
              <Dropdown.Item icon={FiUser}>
                <Link to="/profile">Profile</Link>
              </Dropdown.Item>
              <Dropdown.Item icon={FiSettings}>
                <Link to="/settings">Settings</Link>
              </Dropdown.Item>
              <Dropdown.Divider />
              <Dropdown.Item icon={FiLogOut} onClick={logout}>
                Sign out
              </Dropdown.Item>
            </Dropdown>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;