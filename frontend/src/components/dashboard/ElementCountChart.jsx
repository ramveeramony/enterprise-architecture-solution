import React, { useMemo } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-700 rounded shadow-lg">
        <p className="text-sm text-gray-900 dark:text-white font-medium">{`Date: ${label}`}</p>
        <p className="text-sm text-blue-600 dark:text-blue-400">
          {`Elements: ${payload[0].value}`}
        </p>
      </div>
    );
  }

  return null;
};

const ElementCountChart = ({ data = [] }) => {
  // Format dates for display
  const formattedData = useMemo(() => {
    return data.map(item => {
      // Parse the date
      const date = new Date(item.date);
      
      // Format the date as a more readable string
      const formattedDate = date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
      });
      
      return {
        ...item,
        formattedDate
      };
    });
  }, [data]);
  
  if (!data || data.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <p className="text-gray-500 dark:text-gray-400">No element data available</p>
      </div>
    );
  }

  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={formattedData}
          margin={{
            top: 10,
            right: 30,
            left: 0,
            bottom: 0,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.1} />
          <XAxis 
            dataKey="formattedDate" 
            tick={{ fill: '#6B7280' }}
            tickLine={{ stroke: '#6B7280' }}
            axisLine={{ stroke: '#9CA3AF' }}
          />
          <YAxis 
            tick={{ fill: '#6B7280' }}
            tickLine={{ stroke: '#6B7280' }}
            axisLine={{ stroke: '#9CA3AF' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <defs>
            <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8} />
              <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="count"
            stroke="#3B82F6"
            fillOpacity={1}
            fill="url(#colorCount)"
            strokeWidth={2}
            activeDot={{ r: 8 }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ElementCountChart;