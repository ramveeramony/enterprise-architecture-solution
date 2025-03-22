import React from 'react';
import { Button } from 'flowbite-react';
import { Link } from 'react-router-dom';
import { FiHome, FiArrowLeft } from 'react-icons/fi';

const NotFound = () => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gray-50 dark:bg-gray-900 p-4">
      <div className="text-center">
        <div className="mb-4">
          <h1 className="text-7xl font-bold text-blue-600 dark:text-blue-500">404</h1>
        </div>
        <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Page Not Found
        </h2>
        <p className="text-lg text-gray-500 dark:text-gray-400 mb-8 max-w-md mx-auto">
          The page you are looking for does not exist or has been moved.
        </p>
        
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button as={Link} to="/" gradientDuoTone="purpleToBlue">
            <FiHome className="mr-2 h-5 w-5" />
            Go Home
          </Button>
          <Button
            as={Link}
            to="#"
            onClick={(e) => {
              e.preventDefault();
              window.history.back();
            }}
            color="gray"
          >
            <FiArrowLeft className="mr-2 h-5 w-5" />
            Go Back
          </Button>
        </div>
      </div>
    </div>
  );
};

export default NotFound;