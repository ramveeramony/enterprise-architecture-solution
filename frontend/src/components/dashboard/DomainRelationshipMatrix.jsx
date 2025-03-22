import React, { useMemo } from 'react';
import { Link } from 'react-router-dom';

const DomainRelationshipMatrix = ({ data = [] }) => {
  // Extract unique domains
  const domains = useMemo(() => {
    const allDomains = new Set();
    data.forEach(relation => {
      allDomains.add(relation.source);
      allDomains.add(relation.target);
    });
    return Array.from(allDomains);
  }, [data]);

  // Create a matrix of relationships
  const matrix = useMemo(() => {
    // Initialize matrix with zeros
    const mat = domains.map(() => Array(domains.length).fill(0));
    
    // Fill matrix with relationship values
    data.forEach(relation => {
      const sourceIndex = domains.indexOf(relation.source);
      const targetIndex = domains.indexOf(relation.target);
      if (sourceIndex !== -1 && targetIndex !== -1) {
        mat[sourceIndex][targetIndex] = relation.value;
        // For symmetrical matrix, uncomment the line below
        // mat[targetIndex][sourceIndex] = relation.value;
      }
    });
    
    return mat;
  }, [domains, data]);

  // Calculate color intensity based on value
  const getColorIntensity = (value) => {
    const maxValue = Math.max(...data.map(r => r.value));
    const minValue = Math.min(...data.map(r => r.value));
    const range = maxValue - minValue;
    
    // Calculate intensity (0-100)
    const intensity = range === 0 ? 50 : ((value - minValue) / range) * 100;
    
    return intensity;
  };

  // Get cell color based on value
  const getCellColor = (value) => {
    if (value === 0) return 'bg-gray-100 dark:bg-gray-800';
    
    const intensity = getColorIntensity(value);
    
    // Blue gradient from light to dark
    return `bg-blue-${Math.round((intensity / 100) * 9) * 100} border border-blue-${Math.min(Math.round((intensity / 100) * 9) * 100 + 100, 900)}`;
  };

  // Get text color based on background intensity
  const getTextColor = (value) => {
    const intensity = getColorIntensity(value);
    return intensity > 50 ? 'text-white' : 'text-gray-900 dark:text-white';
  };

  if (!data || data.length === 0 || domains.length === 0) {
    return (
      <div className="flex justify-center items-center h-64">
        <p className="text-gray-500 dark:text-gray-400">No relationship data available</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead>
          <tr>
            <th scope="col" className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Domains
            </th>
            {domains.map((domain, index) => (
              <th 
                key={index} 
                scope="col" 
                className="py-3 px-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                <Link to={`/domains/${domain.toLowerCase()}`} className="hover:underline">
                  {domain}
                </Link>
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
          {domains.map((domain, rowIndex) => (
            <tr key={rowIndex}>
              <td className="py-3 px-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                <Link to={`/domains/${domain.toLowerCase()}`} className="hover:underline">
                  {domain}
                </Link>
              </td>
              {matrix[rowIndex].map((value, colIndex) => (
                <td 
                  key={colIndex} 
                  className={`py-3 px-4 whitespace-nowrap text-sm font-medium ${getCellColor(value)} ${getTextColor(value)} text-center transition-colors duration-200`}
                >
                  {value > 0 ? value : '-'}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DomainRelationshipMatrix;