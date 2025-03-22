import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Flowbite } from 'flowbite-react';
import { AuthProvider } from './services/auth';
import App from './App';
import './index.css';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Theme configuration
const theme = {
  // Customize Flowbite theme
  button: {
    color: {
      primary: 'bg-blue-700 hover:bg-blue-800 focus:ring-blue-300',
    },
  },
};

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Flowbite theme={{ theme }}>
          <App />
        </Flowbite>
      </AuthProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);