import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Sidebar as FlowbiteSidebar } from 'flowbite-react';
import { 
  FiHome, 
  FiLayers, 
  FiDatabase, 
  FiServer, 
  FiBarChart2, 
  FiSettings, 
  FiLink,
  FiCpu,
  FiCompass
} from 'react-icons/fi';

const Sidebar = ({ collapsed, user }) => {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;

  return (
    <div
      className={`${
        collapsed ? 'w-16' : 'w-64'
      } transition-width duration-150 ease-in-out hidden lg:block`}
    >
      <FlowbiteSidebar 
        aria-label="Enterprise Architecture Navigation"
        className="fixed h-screen" 
        collapsed={collapsed}
      >
        <FlowbiteSidebar.Logo
          href="#"
          img="/logo.svg"
          imgAlt="Enterprise Architecture Solution logo"
        >
          {!collapsed && (
            <span className="self-center whitespace-nowrap text-xl font-semibold dark:text-white">
              EA Solution
            </span>
          )}
        </FlowbiteSidebar.Logo>
        <FlowbiteSidebar.Items>
          <FlowbiteSidebar.ItemGroup>
            <FlowbiteSidebar.Item
              as={Link}
              to="/"
              icon={FiHome}
              active={isActive('/')}
            >
              {!collapsed && 'Dashboard'}
            </FlowbiteSidebar.Item>
            
            <FlowbiteSidebar.Item
              as={Link}
              to="/modeling"
              icon={FiLayers}
              active={isActive('/modeling')}
            >
              {!collapsed && 'Modeling'}
            </FlowbiteSidebar.Item>
            
            <FlowbiteSidebar.Item
              as={Link}
              to="/repository"
              icon={FiDatabase}
              active={isActive('/repository')}
            >
              {!collapsed && 'Repository'}
            </FlowbiteSidebar.Item>
          </FlowbiteSidebar.ItemGroup>
          
          <FlowbiteSidebar.ItemGroup>
            <FlowbiteSidebar.Collapse
              icon={FiCompass}
              label={collapsed ? '' : 'Domains'}
            >
              <FlowbiteSidebar.Item 
                as={Link} 
                to="/domains/performance"
                icon={FiBarChart2}
              >
                Performance
              </FlowbiteSidebar.Item>
              <FlowbiteSidebar.Item 
                as={Link} 
                to="/domains/business"
                icon={FiBarChart2}
              >
                Business
              </FlowbiteSidebar.Item>
              <FlowbiteSidebar.Item 
                as={Link} 
                to="/domains/services"
                icon={FiBarChart2}
              >
                Services
              </FlowbiteSidebar.Item>
              <FlowbiteSidebar.Item 
                as={Link} 
                to="/domains/data"
                icon={FiBarChart2}
              >
                Data
              </FlowbiteSidebar.Item>
              <FlowbiteSidebar.Item 
                as={Link} 
                to="/domains/technology"
                icon={FiBarChart2}
              >
                Technology
              </FlowbiteSidebar.Item>
            </FlowbiteSidebar.Collapse>
            
            <FlowbiteSidebar.Item
              as={Link}
              to="/integrations"
              icon={FiLink}
              active={isActive('/integrations')}
            >
              {!collapsed && 'Integrations'}
            </FlowbiteSidebar.Item>
            
            <FlowbiteSidebar.Item
              as={Link}
              to="/ai-features"
              icon={FiCpu}
              active={isActive('/ai-features')}
            >
              {!collapsed && 'AI Features'}
            </FlowbiteSidebar.Item>
          </FlowbiteSidebar.ItemGroup>
          
          <FlowbiteSidebar.ItemGroup>
            <FlowbiteSidebar.Item
              as={Link}
              to="/settings"
              icon={FiSettings}
              active={isActive('/settings')}
            >
              {!collapsed && 'Settings'}
            </FlowbiteSidebar.Item>
          </FlowbiteSidebar.ItemGroup>
        </FlowbiteSidebar.Items>
      </FlowbiteSidebar>
    </div>
  );
};

export default Sidebar;