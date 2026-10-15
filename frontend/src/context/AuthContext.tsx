import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { UserProfile, UserRole } from '@/types/auth';
import { CompanyRegistrationRequestResponse, CompanyResponse } from '@/types/company';
import { authService } from '@/api/auth.service';
import { companyService } from '@/api/company.service';
import { useTelegram } from './TelegramContext';

interface AuthContextValue {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: UserProfile | null;
  role: UserRole;
  activeCompany: CompanyResponse | null;
  pendingRegistration: CompanyRegistrationRequestResponse | null;
  isDevMockMode: boolean;
  loginWithTelegram: (overrideInitData?: string) => Promise<boolean>;
  refreshRegistrations: () => Promise<CompanyRegistrationRequestResponse[]>;
  setDevRole: (newRole: UserRole) => void;
  toggleDevMockMode: (enabled?: boolean) => void;
  setActiveCompany: (company: CompanyResponse | null) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// Platform owner default Telegram ID from backend config
const PLATFORM_OWNER_TID = 5298799880;

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { initData, isInTelegram, initDataUnsafeUser } = useTelegram();

  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [role, setRole] = useState<UserRole>('company_admin');
  const [activeCompany, setActiveCompany] = useState<CompanyResponse | null>(null);
  const [pendingRegistration, setPendingRegistration] = useState<CompanyRegistrationRequestResponse | null>(null);
  const [isDevMockMode, setIsDevMockMode] = useState<boolean>(() => {
    return localStorage.getItem('sp_dev_mock_mode') === 'true';
  });

  const checkUserStatus = useCallback(async (token: string) => {
    try {
      const decoded = authService.decodeToken(token);
      if (!decoded) {
        authService.clearToken();
        setIsAuthenticated(false);
        setIsLoading(false);
        return;
      }

      // Check if user is Platform Owner
      const isOwner = decoded.tid === PLATFORM_OWNER_TID;
      const initialRole: UserRole = isOwner ? 'platform_owner' : 'company_admin';

      setUser({
        id: decoded.sub,
        telegramId: decoded.tid,
        displayName: initDataUnsafeUser?.first_name
          ? `${initDataUnsafeUser.first_name} ${initDataUnsafeUser.last_name || ''}`.trim()
          : `User #${decoded.tid}`,
        username: initDataUnsafeUser?.username,
        role: initialRole,
      });
      setRole(initialRole);
      setIsAuthenticated(true);

      // Fetch user's company registrations from real backend
      try {
        const registrations = await companyService.getMyRegistrations();
        if (registrations && registrations.length > 0) {
          const latest = registrations[0];
          setPendingRegistration(latest);

          // If approved or active, load company details
          if (latest.status === 'approved' || latest.status === 'active') {
            try {
              const comp = await companyService.getCompany(latest.id);
              setActiveCompany(comp);
            } catch {
              // Might still be pending creation in backend
            }
          }
        }
      } catch (err) {
        console.warn('Could not fetch registrations:', err);
      }
    } catch (err) {
      console.error('Failed to restore session:', err);
      authService.clearToken();
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, [initDataUnsafeUser]);

  // Initial check on mount
  useEffect(() => {
    const existingToken = authService.getToken();
    if (existingToken) {
      checkUserStatus(existingToken);
    } else if (isInTelegram && initData) {
      // Auto-authenticate inside Telegram with raw initData
      loginWithTelegram(initData);
    } else {
      setIsLoading(false);
    }
  }, [isInTelegram, initData, checkUserStatus]);

  const loginWithTelegram = async (overrideInitData?: string): Promise<boolean> => {
    setIsLoading(true);
    // Always check for the freshest initData directly from window.Telegram
    const freshTgData = window.Telegram?.WebApp?.initData;
    const dataToUse = overrideInitData || (freshTgData && freshTgData.trim().length > 0 ? freshTgData : initData);

    try {
      if (!dataToUse) {
        throw new Error('No Telegram initData found. Please open this app inside Telegram.');
      }

      const response = await authService.authenticateTelegram(dataToUse);
      if (response?.access_token) {
        await checkUserStatus(response.access_token);
        return true;
      }
      return false;
    } catch (err: any) {
      console.error('Telegram auth error:', err);
      setIsLoading(false);
      if (err?.code === 'INIT_DATA_EXPIRED' || err?.message?.toLowerCase().includes('expired')) {
        throw new Error(
          'Your Telegram session has expired. Please completely close this Mini App window in Telegram (tap ✕) and reopen it from the bot.'
        );
      }
      throw err;
    }
  };

  const refreshRegistrations = async (): Promise<CompanyRegistrationRequestResponse[]> => {
    try {
      const registrations = await companyService.getMyRegistrations();
      if (registrations && registrations.length > 0) {
        setPendingRegistration(registrations[0]);
      }
      return registrations || [];
    } catch (err) {
      console.warn('Failed to refresh registrations:', err);
      return [];
    }
  };

  const setDevRole = (newRole: UserRole) => {
    setRole(newRole);
    if (user) {
      setUser({ ...user, role: newRole });
    }
  };

  const toggleDevMockMode = (enabled?: boolean) => {
    const nextVal = enabled !== undefined ? enabled : !isDevMockMode;
    setIsDevMockMode(nextVal);
    localStorage.setItem('sp_dev_mock_mode', String(nextVal));
  };

  const logout = () => {
    authService.clearToken();
    setIsAuthenticated(false);
    setUser(null);
    setActiveCompany(null);
    setPendingRegistration(null);
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        isLoading,
        user,
        role,
        activeCompany,
        pendingRegistration,
        isDevMockMode,
        loginWithTelegram,
        refreshRegistrations,
        setDevRole,
        toggleDevMockMode,
        setActiveCompany,
        logout,
      }}
    >
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
