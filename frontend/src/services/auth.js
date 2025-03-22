/**
 * Enterprise Architecture Solution - Auth Service
 * 
 * This module provides authentication functionality using Supabase and Microsoft Entra ID.
 */

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY;
const supabase = createClient(supabaseUrl, supabaseKey);

// Create context
const AuthContext = createContext(null);

/**
 * Auth provider component
 */
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Initialize auth
  const initAuth = useCallback(async () => {
    setLoading(true);
    
    try {
      // Check for existing session
      const { data: { session } } = await supabase.auth.getSession();
      
      if (session) {
        const { data: userProfile } = await supabase
          .from('users')
          .select('*')
          .eq('id', session.user.id)
          .single();
          
        setUser({
          ...session.user,
          profile: userProfile || {}
        });
      }
    } catch (error) {
      console.error('Error initializing auth:', error);
    } finally {
      setLoading(false);
    }
    
    // Setup auth state change listener
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (session) {
          // Fetch user profile
          const { data: userProfile } = await supabase
            .from('users')
            .select('*')
            .eq('id', session.user.id)
            .single();
            
          setUser({
            ...session.user,
            profile: userProfile || {}
          });
        } else {
          setUser(null);
        }
        
        setLoading(false);
      }
    );
    
    // Cleanup on unmount
    return () => {
      subscription.unsubscribe();
    };
  }, []);
  
  // Login with Entra ID
  const loginWithEntraId = useCallback(async () => {
    setLoading(true);
    
    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'azure',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
        },
      });
      
      if (error) {
        throw error;
      }
      
      return data;
    } catch (error) {
      console.error('Error logging in with Entra ID:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);
  
  // Login with email and password
  const loginWithEmailPassword = useCallback(async (email, password) => {
    setLoading(true);
    
    try {
      // For development purposes, use a mock user if no Supabase is available
      if (import.meta.env.DEV && (!supabaseUrl || !supabaseKey)) {
        console.warn('Using mock authentication in development');
        
        // Mock authentication for development
        if (email === 'admin@example.com' && password === 'password') {
          const mockUser = {
            id: 'mock-user-id',
            email: 'admin@example.com',
            user_metadata: {
              full_name: 'Admin User'
            },
            profile: {
              role: 'admin'
            }
          };
          
          setUser(mockUser);
          localStorage.setItem('auth_token', 'mock-token');
          return { user: mockUser };
        } else {
          throw new Error('Invalid email or password');
        }
      }
      
      // Real authentication with Supabase
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });
      
      if (error) {
        throw error;
      }
      
      return data;
    } catch (error) {
      console.error('Error logging in with email/password:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);
  
  // Logout
  const logout = useCallback(async () => {
    setLoading(true);
    
    try {
      // For development with mock auth
      if (import.meta.env.DEV && (!supabaseUrl || !supabaseKey)) {
        console.warn('Using mock logout in development');
        setUser(null);
        localStorage.removeItem('auth_token');
        return;
      }
      
      // Real logout with Supabase
      const { error } = await supabase.auth.signOut();
      
      if (error) {
        throw error;
      }
    } catch (error) {
      console.error('Error logging out:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);
  
  // Check if user is authenticated
  const isAuthenticated = Boolean(user);
  
  // Auth context value
  const value = {
    user,
    loading,
    isAuthenticated,
    initAuth,
    loginWithEntraId,
    loginWithEmailPassword,
    logout
  };
  
  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

/**
 * Custom hook to use auth context
 */
export const useAuth = () => {
  const context = useContext(AuthContext);
  
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};

/**
 * Helper function to export auth functionality
 */
export default {
  AuthProvider,
  useAuth
};