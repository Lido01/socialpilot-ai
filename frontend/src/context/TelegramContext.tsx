import React, { createContext, useContext, useEffect, useState } from 'react';
import { TelegramWebAppObject, TelegramWebUser } from '@/types/telegram';

interface TelegramContextValue {
  tg: TelegramWebAppObject | null;
  isInTelegram: boolean;
  initData: string;
  initDataUnsafeUser: TelegramWebUser | null;
  colorScheme: 'light' | 'dark';
  haptic: (style?: 'light' | 'medium' | 'heavy' | 'success' | 'error') => void;
  setBackButton: (visible: boolean, onClick?: () => void) => void;
}

const TelegramContext = createContext<TelegramContextValue | null>(null);

export const TelegramProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [tg, setTg] = useState<TelegramWebAppObject | null>(null);
  const [initData, setInitData] = useState<string>('');
  const [initDataUnsafeUser, setInitDataUnsafeUser] = useState<TelegramWebUser | null>(null);
  const [colorScheme, setColorScheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    const webApp = window.Telegram?.WebApp;
    if (webApp && webApp.initData) {
      setTg(webApp);
      setInitData(webApp.initData);
      setInitDataUnsafeUser(webApp.initDataUnsafe?.user || null);
      setColorScheme(webApp.colorScheme || 'light');

      try {
        webApp.ready();
        webApp.expand();
        webApp.setHeaderColor('#ffffff');
        webApp.setBackgroundColor('#f8fafc');
      } catch (err) {
        console.warn('Telegram WebApp initialization error:', err);
      }
    } else {
      // Check query params if opened with ?tgWebAppData=...
      const urlParams = new URLSearchParams(window.location.search);
      const paramData = urlParams.get('tgWebAppData');
      if (paramData) {
        setInitData(paramData);
      }
    }
  }, []);

  const haptic = (style: 'light' | 'medium' | 'heavy' | 'success' | 'error' = 'light') => {
    if (!tg?.HapticFeedback) return;
    try {
      if (style === 'success' || style === 'error') {
        tg.HapticFeedback.notificationOccurred(style);
      } else {
        tg.HapticFeedback.impactOccurred(style);
      }
    } catch {
      // Haptics optional
    }
  };

  const setBackButton = (visible: boolean, onClick?: () => void) => {
    if (!tg?.BackButton) return;
    try {
      if (visible) {
        tg.BackButton.show();
        if (onClick) {
          tg.BackButton.onClick(onClick);
        }
      } else {
        tg.BackButton.hide();
      }
    } catch {
      // Ignore if not supported
    }
  };

  return (
    <TelegramContext.Provider
      value={{
        tg,
        isInTelegram: Boolean(tg && initData),
        initData,
        initDataUnsafeUser,
        colorScheme,
        haptic,
        setBackButton,
      }}
    >
      {children}
    </TelegramContext.Provider>
  );
};

export const useTelegram = () => {
  const context = useContext(TelegramContext);
  if (!context) {
    throw new Error('useTelegram must be used within a TelegramProvider');
  }
  return context;
};
