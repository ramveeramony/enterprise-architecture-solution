import React from 'react';
import { Card, Badge, Button, Dropdown } from 'flowbite-react';
import { FiActivity, FiLayers, FiDatabase, FiServer, FiBarChart2, FiList, FiTrendingUp, FiPlus } from 'react-icons/fi';
import { useQuery } from '@tanstack/react-query';

// Custom components
import DomainSummaryCard from '../components/dashboard/DomainSummaryCard';
import RecentActivity from '../components/dashboard/RecentActivity';
import ElementCountChart from '../components/dashboard/ElementCountChart';
import DomainRelationshipMatrix from '../components/dashboard/DomainRelationshipMatrix';

// Services
import { fetchDashboardStats, fetchRecentActivity } from '../services/dashboard';

const Dashboard = () => {
  // Fetch dashboard statistics
  const { 
    data: stats, 
    isLoading: statsLoading,
    error: statsError
  } = useQuery({
    queryKey: ['dashboardStats'],
    queryFn: fetchDashboardStats
  });

  // Fetch recent activity
  const { 
    data: recentActivity, 
    isLoading: activityLoading,
    error: activityError
  } = useQuery({
    queryKey: ['recentActivity'],
    queryFn: fetchRecentActivity
  });

  // Handle loading states
  if (statsLoading || activityLoading) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <div className="text-center">
          <div className="mb-4 h-12 w-12 animate-spin rounded-full border-4 border-blue-600 border-t-transparent mx-auto"></div>
          <p className="text-gray-700">Loading dashboard data...</p>
        </div>
      </div>
    );
  }

  // Handle error states
  if (statsError || activityError) {
    return (
      <div className="flex h-full items-center justify-center p-4">
        <Card className="max-w-md">
          <h5 className="text-xl font-bold tracking-tight text-gray-900 dark:text-white">
            Error Loading Data
          </h5>
          <p className="font-normal text-gray-700 dark:text-gray-400">
            There was an error loading the dashboard data. Please try again later.
          </p>
          <Button onClick={() => window.location.reload()}>
            Retry
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-4 bg-gray-50 dark:bg-gray-900 min-h-screen">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-gray-900 dark:text-white">Enterprise Architecture Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Overview of your enterprise architecture models and artifacts
          </p>
        </div>
        <div className="flex space-x-2">
          <Dropdown label="Filter by Domain" dismissOnClick={true}>
            <Dropdown.Item>All Domains</Dropdown.Item>
            <Dropdown.Item>Business</Dropdown.Item>
            <Dropdown.Item>Data</Dropdown.Item>
            <Dropdown.Item>Application</Dropdown.Item>
            <Dropdown.Item>Technology</Dropdown.Item>
          </Dropdown>
          <Button gradientDuoTone="purpleToBlue">
            <FiPlus className="mr-2 h-5 w-5" />
            Create New
          </Button>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-6">
        <DomainSummaryCard 
          icon={<FiBarChart2 className="h-6 w-6" />}
          title="Performance" 
          count={stats?.domains?.performance || 0}
          color="blue"
        />
        <DomainSummaryCard 
          icon={<FiActivity className="h-6 w-6" />}
          title="Business" 
          count={stats?.domains?.business || 0}
          color="green"
        />
        <DomainSummaryCard 
          icon={<FiList className="h-6 w-6" />}
          title="Services" 
          count={stats?.domains?.services || 0}
          color="purple"
        />
        <DomainSummaryCard 
          icon={<FiDatabase className="h-6 w-6" />}
          title="Data" 
          count={stats?.domains?.data || 0}
          color="yellow"
        />
        <DomainSummaryCard 
          icon={<FiTrendingUp className="h-6 w-6" />}
          title="Technology" 
          count={stats?.domains?.technology || 0}
          color="red"
        />
      </div>

      {/* Charts and activity */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3 mb-6">
        <Card className="lg:col-span-2">
          <div className="mb-2 flex items-center justify-between">
            <h5 className="text-xl font-bold leading-none text-gray-900 dark:text-white">
              Element Distribution
            </h5>
            <Badge color="gray">Last 30 days</Badge>
          </div>
          <ElementCountChart data={stats?.elementCounts || []} />
        </Card>
        <Card>
          <div className="mb-2 flex items-center justify-between">
            <h5 className="text-xl font-bold leading-none text-gray-900 dark:text-white">
              Recent Activity
            </h5>
            <Button size="xs">View all</Button>
          </div>
          <RecentActivity activities={recentActivity || []} />
        </Card>
      </div>

      {/* Domain relationship matrix */}
      <Card>
        <div className="mb-2 flex items-center justify-between">
          <h5 className="text-xl font-bold leading-none text-gray-900 dark:text-white">
            Domain Relationship Matrix
          </h5>
          <Badge color="gray">Current State</Badge>
        </div>
        <DomainRelationshipMatrix data={stats?.relationshipMatrix || []} />
      </Card>
    </div>
  );
};

export default Dashboard;
