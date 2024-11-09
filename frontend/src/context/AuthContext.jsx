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

    const handleLogout = () => {
        logout({
            logoutParams: {
                returnTo: window.location.origin
            }
        });
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
        isLoading: isLoading,
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
