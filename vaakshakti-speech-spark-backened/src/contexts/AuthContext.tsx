import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiService, UserRead, TokenResponse } from '@/services/api';

export interface AuthContextType { // Added export
  currentUser: UserRead | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<TokenResponse>;
  register: (email: string, password: string, fullName?: string) => Promise<UserRead>;
  logout: () => void;
  fetchCurrentUser: () => Promise<UserRead | null>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<UserRead | null>(null);
  // Token state now reflects the accessToken from localStorage, managed by apiService
  const [token, setToken] = useState<string | null>(localStorage.getItem("accessToken"));
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchCurrentUser = async (retrying: boolean = false): Promise<UserRead | null> => {
    const currentAccessToken = localStorage.getItem("accessToken");
    if (currentAccessToken) {
      setToken(currentAccessToken); // Ensure token state is up-to-date
      try {
        const user = await apiService.getCurrentUser();
        setCurrentUser(user);
        return user;
      } catch (error: any) {
        console.error("Failed to fetch current user:", error.message);
        // If 401 and not already retrying, attempt refresh
        if (error.message.includes("401") && !retrying) {
          console.log("Attempting token refresh from AuthContext...");
          const newTokens = await apiService.refreshToken();
          if (newTokens) {
            return fetchCurrentUser(true); // Retry fetching user with new token
          } else {
            // Refresh failed, logout is handled by apiService.refreshToken()
            setCurrentUser(null);
            setToken(null);
            return null;
          }
        } else {
          // For other errors or if already retried, logout
          apiService.logoutUser();
          setCurrentUser(null);
          setToken(null);
          return null;
        }
      }
    }
    // No token initially, or refresh failed and tokens cleared
    setCurrentUser(null);
    setToken(null);
    return null;
  };
  
  useEffect(() => {
    const initializeAuth = async () => {
      setIsLoading(true);
      await fetchCurrentUser();
      setIsLoading(false);
    };
    initializeAuth();
  }, []);

  const login = async (email: string, password: string): Promise<TokenResponse> => {
    setIsLoading(true);
    try {
      const tokenResponse = await apiService.loginUser(email, password);
      // apiService.loginUser now stores tokens in localStorage
      setToken(localStorage.getItem("accessToken")); // Update AuthContext's token state
      await fetchCurrentUser();
      setIsLoading(false);
      return tokenResponse;
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  const register = async (email: string, password: string, fullName?: string): Promise<UserRead> => {
    setIsLoading(true);
    try {
      const user = await apiService.registerUser(email, password, fullName);
      // Optionally log in the user directly after registration
      // await login(email, password); 
      setIsLoading(false);
      return user;
    } catch (error) {
      setIsLoading(false);
      throw error;
    }
  };

  const logout = async () => { // Made this function async
    await apiService.logoutUser(); // apiService.logoutUser now handles localStorage removal
    setCurrentUser(null);
    setToken(null); // Clear token state in AuthContext
  };

  const isAuthenticated = !!localStorage.getItem("accessToken") && !!currentUser;


  return (
    <AuthContext.Provider
      value={{
        currentUser,
        token: localStorage.getItem("accessToken"), // Provide current accessToken
        isLoading,
        isAuthenticated,
        login,
        register,
        logout,
        fetchCurrentUser
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};