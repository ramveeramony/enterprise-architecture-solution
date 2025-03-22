import { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { createClient } from '@supabase/supabase-js';
import * as msal from 'msal-browser';

// Initialize Supabase client
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

// Initialize Microsoft Authentication Library
const msalConfig = {
  auth: {
    clientId: import.meta.env.VITE_MS_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_MS_TENANT_ID}`,
    redirectUri: import.meta.env.VITE_MS_REDIRECT_URI,
  },
  cache: {
    cacheLocation: 'localStorage',
    storeAuthStateInCookie: false,
  },
};

// Create MSAL Instance
let msalInstance = null;
try {
  msalInstance = new msal.PublicClientApplication(msalConfig);
} catch (error) {
  console.error('Error initializing MSAL:', error);
}

// Authentication context
const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Initialize authentication
  const initAuth = useCallback(async () => {
    try {
      setLoading(true);

      // Check if user is already authenticated with Supabase
      const { data: { session }, error } = await supabase.auth.getSession();
      
      if (session) {
        // Get user profile data
        const { data: profile } = await supabase
          .from('users')
          .select('*')
          .eq('id', session.user.id)
          .single();

        setUser({
          id: session.user.id,
          email: session.user.email,
          name: profile?.full_name || session.user.email,
          role: profile?.role || 'viewer',
          provider: 'supabase',
        });
      } else if (msalInstance) {
        // Check if user is authenticated with Microsoft
        const accounts = msalInstance.getAllAccounts();
        if (accounts.length > 0) {
          const account = accounts[0];
          
          // Get or create user in Supabase
          const { data: existingUser, error: userError } = await supabase
            .from('users')
            .select('*')
            .eq('email', account.username)
            .single();
            
          if (existingUser) {
            setUser({
              id: existingUser.id,
              email: account.username,
              name: account.name || account.username,
              role: existingUser.role || 'viewer',
              provider: 'microsoft',
            });
          } else {
            // If not found in Supabase, we'll create a user when they log in
            setUser({
              email: account.username,
              name: account.name || account.username,
              role: 'viewer',
              provider: 'microsoft',
            });
          }
        }
      }
    } catch (error) {
      console.error('Error initializing auth:', error);
    } finally {
      setLoading(false);
    }
    
    return true;
  }, []);

  // Subscribe to auth state changes
  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (event, session) => {
        if (event === 'SIGNED_IN' && session) {
          // Update user state
          setUser({
            id: session.user.id,
            email: session.user.email,
            role: 'viewer', // Default role
            provider: 'supabase',
          });
          
          // Get user profile
          supabase
            .from('users')
            .select('*')
            .eq('id', session.user.id)
            .single()
            .then(({ data }) => {
              if (data) {
                setUser(prev => ({
                  ...prev,
                  name: data.full_name || prev.email,
                  role: data.role || 'viewer',
                }));
              }
            });
        } else if (event === 'SIGNED_OUT') {
          setUser(null);
        }
      }
    );

    return () => {
      subscription?.unsubscribe();
    };
  }, []);

  // Register with email and password
  const register = async (email, password, fullName) => {
    try {
      // Sign up with Supabase
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
      });

      if (error) throw error;

      // Create user profile
      if (data.user) {
        const { error: profileError } = await supabase
          .from('users')
          .insert([
            {
              id: data.user.id,
              email: data.user.email,
              full_name: fullName,
              role: 'viewer',
            },
          ]);

        if (profileError) throw profileError;
      }

      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  // Login with email and password
  const login = async (email, password) => {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (error) throw error;

      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  // Login with Microsoft Entra ID
  const loginWithMicrosoft = async () => {
    if (!msalInstance) {
      return { success: false, error: 'Microsoft authentication not configured' };
    }

    try {
      const loginRequest = {
        scopes: ['user.read'],
      };
      
      const response = await msalInstance.loginPopup(loginRequest);
      
      if (response) {
        // Check if user exists in Supabase
        const { data: existingUser, error: userError } = await supabase
          .from('users')
          .select('*')
          .eq('email', response.account.username)
          .single();
        
        if (!existingUser) {
          // Create user in Supabase
          const { data: authUser, error: authError } = await supabase.auth.signUp({
            email: response.account.username,
            password: Math.random().toString(36).slice(-8), // Generate random password
          });

          if (authError) throw authError;
          
          // Create user profile
          if (authUser?.user) {
            const { error: profileError } = await supabase
              .from('users')
              .insert([
                {
                  id: authUser.user.id,
                  email: response.account.username,
                  full_name: response.account.name || response.account.username,
                  role: 'viewer',
                },
              ]);

            if (profileError) throw profileError;
          }
        }
        
        // Set user state
        setUser({
          id: existingUser?.id,
          email: response.account.username,
          name: response.account.name || response.account.username,
          role: existingUser?.role || 'viewer',
          provider: 'microsoft',
        });

        return { success: true };
      }
      
      return { success: false, error: 'Login failed' };
    } catch (error) {
      console.error('Microsoft login error:', error);
      return { success: false, error: error.message };
    }
  };

  // Logout
  const logout = async () => {
    try {
      // Sign out from Supabase
      const { error } = await supabase.auth.signOut();
      if (error) throw error;

      // Sign out from Microsoft if applicable
      if (msalInstance && user?.provider === 'microsoft') {
        await msalInstance.logout();
      }

      setUser(null);
      return { success: true };
    } catch (error) {
      console.error('Logout error:', error);
      return { success: false, error: error.message };
    }
  };

  // Check if user is authenticated
  const isAuthenticated = !!user;

  const value = {
    user,
    loading,
    isAuthenticated,
    register,
    login,
    loginWithMicrosoft,
    logout,
    initAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Hook to use auth context
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};