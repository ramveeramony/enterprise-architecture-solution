import React from 'react';
import { Breadcrumb } from 'flowbite-react';
import { FiHome, FiCpu } from 'react-icons/fi';

import GenAIFeatures from '../components/genai/GenAIFeatures';

/**
 * GenAI Page component provides access to AI capabilities
 */
const GenAIPage = () => {
  return (
    <div className="p-4">
      <div className="mb-4">
        <Breadcrumb>
          <Breadcrumb.Item href="/" icon={FiHome}>
            Home
          </Breadcrumb.Item>
          <Breadcrumb.Item icon={FiCpu}>
            GenAI Features
          </Breadcrumb.Item>
        </Breadcrumb>
      </div>
      
      <div className="mb-4">
        <h1 className="text-2xl font-bold">AI-Powered Architecture Features</h1>
        <p className="text-gray-600">
          Leverage AI capabilities to enhance your enterprise architecture
        </p>
      </div>
      
      <GenAIFeatures />
    </div>
  );
};

export default GenAIPage;