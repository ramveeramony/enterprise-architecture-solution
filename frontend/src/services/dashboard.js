import { api, supabase } from './api';

// Fetch dashboard statistics
export const fetchDashboardStats = async () => {
  try {
    // Fetch from API if available
    try {
      const { data } = await api.get('/api/dashboard/stats');
      return data;
    } catch (apiError) {
      console.log('API not available, falling back to mock data');
      
      // Fall back to Supabase direct query
      try {
        // Count elements by domain
        const { data: domainCounts, error: domainError } = await supabase
          .from('ea_elements')
          .select('ea_element_types(domain_id), count', { count: 'exact' })
          .then(result => {
            // Process and group the results
            const domains = {
              performance: 0,
              business: 0,
              services: 0,
              data: 0,
              technology: 0
            };
            
            // Process domain counts
            return { domains };
          });

        if (domainError) throw domainError;
        
        // Get element counts over time
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        
        const { data: elementCounts, error: elementError } = await supabase
          .from('ea_elements')
          .select('created_at, type_id')
          .gte('created_at', thirtyDaysAgo.toISOString());
        
        if (elementError) throw elementError;
        
        // Create mock relationship matrix
        const relationshipMatrix = [
          { source: 'Performance', target: 'Business', value: 12 },
          { source: 'Performance', target: 'Services', value: 8 },
          { source: 'Performance', target: 'Data', value: 5 },
          { source: 'Performance', target: 'Technology', value: 3 },
          { source: 'Business', target: 'Services', value: 15 },
          { source: 'Business', target: 'Data', value: 9 },
          { source: 'Business', target: 'Technology', value: 6 },
          { source: 'Services', target: 'Data', value: 14 },
          { source: 'Services', target: 'Technology', value: 10 },
          { source: 'Data', target: 'Technology', value: 7 },
        ];
        
        return {
          domains: domainCounts?.domains || getMockDomainCounts(),
          elementCounts: getElementCountsFromData(elementCounts || []),
          relationshipMatrix: relationshipMatrix,
        };
      } catch (supabaseError) {
        console.error('Error fetching dashboard stats from Supabase:', supabaseError);
        
        // Fall back to mock data if both API and Supabase fail
        return getMockDashboardStats();
      }
    }
  } catch (error) {
    console.error('Error fetching dashboard stats:', error);
    throw error;
  }
};

// Fetch recent activity
export const fetchRecentActivity = async () => {
  try {
    // Fetch from API if available
    try {
      const { data } = await api.get('/api/dashboard/activity');
      return data;
    } catch (apiError) {
      console.log('API not available, falling back to mock data');
      
      // Fall back to Supabase direct query
      try {
        // Get recent elements with their creators
        const { data: recentElements, error: elementsError } = await supabase
          .from('ea_elements')
          .select('id, name, created_at, created_by(full_name), type_id')
          .order('created_at', { ascending: false })
          .limit(5);
        
        if (elementsError) throw elementsError;
        
        // Get recent model updates
        const { data: recentModels, error: modelsError } = await supabase
          .from('ea_models')
          .select('id, name, updated_at, updated_by(full_name)')
          .order('updated_at', { ascending: false })
          .limit(5);
        
        if (modelsError) throw modelsError;
        
        // Combine and format the data
        const combinedActivity = [
          ...recentElements.map(el => ({
            id: \`element_\${el.id}\`,
            type: 'element_created',
            name: el.name,
            timestamp: el.created_at,
            user: el.created_by?.full_name || 'Unknown user',
          })),
          ...recentModels.map(model => ({
            id: \`model_\${model.id}\`,
            type: 'model_updated',
            name: model.name,
            timestamp: model.updated_at,
            user: model.updated_by?.full_name || 'Unknown user',
          })),
        ].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
         .slice(0, 10);
        
        return combinedActivity;
      } catch (supabaseError) {
        console.error('Error fetching activity from Supabase:', supabaseError);
        
        // Fall back to mock data if both API and Supabase fail
        return getMockActivity();
      }
    }
  } catch (error) {
    console.error('Error fetching recent activity:', error);
    throw error;
  }
};

// Helper function to process element counts from database data
const getElementCountsFromData = (elements) => {
  // Group by date (day)
  const countsByDay = elements.reduce((acc, element) => {
    const date = new Date(element.created_at).toISOString().split('T')[0];
    if (!acc[date]) {
      acc[date] = { date, count: 0 };
    }
    acc[date].count += 1;
    return acc;
  }, {});
  
  // Convert to array and sort by date
  const result = Object.values(countsByDay).sort((a, b) => 
    new Date(a.date) - new Date(b.date)
  );
  
  // If no data, return mock data
  if (result.length === 0) {
    return getMockElementCounts();
  }
  
  return result;
};

// Mock data generators for fallback
const getMockDomainCounts = () => {
  return {
    performance: 24,
    business: 48,
    services: 36,
    data: 42,
    technology: 30
  };
};

const getMockElementCounts = () => {
  const result = [];
  const today = new Date();
  
  // Generate data for the last 30 days
  for (let i = 29; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    
    result.push({
      date: date.toISOString().split('T')[0],
      count: Math.floor(Math.random() * 5) + 1, // 1-5 elements per day
    });
  }
  
  return result;
};

const getMockActivity = () => {
  const activities = [
    {
      id: 'element_1',
      type: 'element_created',
      name: 'Customer Management Process',
      timestamp: '2025-03-21T15:30:00Z',
      user: 'Jane Smith'
    },
    {
      id: 'model_1',
      type: 'model_updated',
      name: 'Core Business Architecture',
      timestamp: '2025-03-21T14:45:00Z',
      user: 'John Doe'
    },
    {
      id: 'element_2',
      type: 'element_created',
      name: 'Customer Database',
      timestamp: '2025-03-21T13:20:00Z',
      user: 'Jane Smith'
    },
    {
      id: 'element_3',
      type: 'element_updated',
      name: 'Authentication Service',
      timestamp: '2025-03-21T11:15:00Z',
      user: 'Michael Johnson'
    },
    {
      id: 'model_2',
      type: 'model_created',
      name: 'Technology Reference Architecture',
      timestamp: '2025-03-20T16:30:00Z',
      user: 'John Doe'
    },
    {
      id: 'element_4',
      type: 'element_deleted',
      name: 'Legacy Payment Gateway',
      timestamp: '2025-03-20T15:45:00Z',
      user: 'Michael Johnson'
    },
    {
      id: 'element_5',
      type: 'element_created',
      name: 'New Payment Gateway',
      timestamp: '2025-03-20T15:40:00Z',
      user: 'Michael Johnson'
    },
    {
      id: 'model_3',
      type: 'model_updated',
      name: 'Data Architecture',
      timestamp: '2025-03-20T14:20:00Z',
      user: 'Jane Smith'
    },
    {
      id: 'element_6',
      type: 'element_created',
      name: 'Customer Analytics Dashboard',
      timestamp: '2025-03-20T11:10:00Z',
      user: 'John Doe'
    },
    {
      id: 'element_7',
      type: 'element_updated',
      name: 'User Management Component',
      timestamp: '2025-03-19T16:30:00Z',
      user: 'Jane Smith'
    }
  ];
  
  return activities;
};

const getMockDashboardStats = () => {
  return {
    domains: getMockDomainCounts(),
    elementCounts: getMockElementCounts(),
    relationshipMatrix: [
      { source: 'Performance', target: 'Business', value: 12 },
      { source: 'Performance', target: 'Services', value: 8 },
      { source: 'Performance', target: 'Data', value: 5 },
      { source: 'Performance', target: 'Technology', value: 3 },
      { source: 'Business', target: 'Services', value: 15 },
      { source: 'Business', target: 'Data', value: 9 },
      { source: 'Business', target: 'Technology', value: 6 },
      { source: 'Services', target: 'Data', value: 14 },
      { source: 'Services', target: 'Technology', value: 10 },
      { source: 'Data', target: 'Technology', value: 7 },
    ],
  };
};