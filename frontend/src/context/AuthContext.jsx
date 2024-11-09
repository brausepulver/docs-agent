import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL;

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
    const {
        isAuthenticated,
        loginWithRedirect,
        logout,
        getAccessTokenSilently,
        user,
        isLoading
    } = useAuth0();

    const [userProfile, setUserProfile] = useState(null);
    const [authLoading, setAuthLoading] = useState(true);

    useEffect(() => {
        const getUserProfile = async () => {
            if (isAuthenticated && user) {
                try {
                    const token = await getAccessTokenSilently();

                    // Create an axios instance for authenticated requests
                    const authAxios = axios.create({
                        baseURL: API_URL,
                        headers: {
                            Authorization: `Bearer ${token}`
                        }
                    });

                    // Fetch user profile from your backend
                    const response = await authAxios.get('/api/auth/user-profile');
                    setUserProfile(response.data);
                } catch (error) {
                    console.error('Error fetching user profile:', error);
                    // Handle error appropriately - maybe set an error state
                }
            }
            setAuthLoading(false);
        };

        if (!isLoading) {
            getUserProfile();
        }
    }, [isAuthenticated, user, getAccessTokenSilently, isLoading]);

    const handleLogout = () => {
        logout({
            logoutParams: {
                returnTo: window.location.origin
            }
        });
        setUserProfile(null);
    };

    // Create authenticated axios instance
    const createAuthenticatedAxios = async () => {
        const token = await getAccessTokenSilently();
        return axios.create({
            baseURL: API_URL,
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
    };

    const value = {
        isAuthenticated,
        login: loginWithRedirect,
        logout: handleLogout,
        user,
        userProfile,
        isLoading: isLoading || authLoading,
        createAuthenticatedAxios
    };

    return (
        <AuthContext.Provider value={value}>
        {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
