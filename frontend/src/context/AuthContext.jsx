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

    const [isAuthLoading, setIsAuthLoading] = useState(true);

    const createAuthenticatedAxios = async () => {
        const token = await getAccessTokenSilently();
        return axios.create({
            baseURL: API_URL,
            headers: {
                Authorization: `Bearer ${token}`
            }
        });
    };

    useEffect(() => {
        const login = async () => {
            if (isAuthenticated && user) {
                try {
                    const axios = await createAuthenticatedAxios();
                    await axios.post(`${import.meta.env.VITE_API_URL}/auth/login`);
                } catch (error) {
                    console.error('Error logging in:', error);
                }
            }
            setIsAuthLoading(false);
        };

        if (!isLoading) {
            login();
        }
    }, [isAuthenticated, user, getAccessTokenSilently, isLoading]);

    const handleLogout = () => {
        logout({
            logoutParams: {
                returnTo: window.location.origin
            }
        });
    };

    const value = {
        isAuthenticated,
        login: loginWithRedirect,
        logout: handleLogout,
        user,
        isLoading: isLoading,
        createAuthenticatedAxios,
        isAuthLoading
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
