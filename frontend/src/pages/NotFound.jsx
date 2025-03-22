import React from 'react';
import { Button } from 'flowbite-react';
import { Link } from 'react-router-dom';
import { FiHome } from 'react-icons/fi';

/**
 * Not Found (404) page component
 */
const NotFound = () => {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gray-100 p-4 text-center">
      <h1 className="mb-4 text-9xl font-bold text-blue-600">404</h1>
      <h2 className="mb-4 text-3xl font-semibold">Page Not Found</h2>
      <p className="mb-8 max-w-md text-gray-600">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <Button as={Link} to="/" color="blue">
        <FiHome className="mr-2 h-5 w-5" />
        Back to Home
      </Button>
    </div>
  );
};

export default NotFound;