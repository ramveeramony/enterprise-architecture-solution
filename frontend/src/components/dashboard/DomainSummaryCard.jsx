import React from 'react';
import { Card } from 'flowbite-react';
import { Link } from 'react-router-dom';

const colorMap = {
  blue: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300',
  green: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
  red: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
  yellow: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
  purple: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-300',
  indigo: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-300',
  pink: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-300',
};

const DomainSummaryCard = ({ title, count, icon, color = 'blue' }) => {
  const colorClass = colorMap[color] || colorMap.blue;
  const domainPath = title.toLowerCase();

  return (
    <Card className="hover:shadow-lg transition-shadow duration-300 cursor-pointer">
      <Link to={`/domains/${domainPath}`} className="block">
        <div className="flex items-center">
          <div className={`p-3 mr-4 rounded-full ${colorClass}`}>
            {icon}
          </div>
          <div>
            <div className="text-2xl font-bold text-gray-900 dark:text-white">
              {count}
            </div>
            <div className="font-medium text-gray-500 dark:text-gray-400">
              {title}
            </div>
          </div>
        </div>
      </Link>
    </Card>
  );
};

export default DomainSummaryCard;