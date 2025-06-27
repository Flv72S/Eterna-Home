import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface House {
  house_id: number;
  house_name: string;
  house_address: string;
  role_in_house?: string;
  is_owner: boolean;
  is_active: boolean;
  created_at: string;
}

interface HouseContextType {
  activeHouseId: number | null;
  setActiveHouseId: (houseId: number | null) => void;
  availableHouses: House[];
  setAvailableHouses: (houses: House[]) => void;
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  refreshHouses: () => Promise<void>;
}

const HouseContext = createContext<HouseContextType | undefined>(undefined);

interface HouseProviderProps {
  children: ReactNode;
}

export const HouseProvider: React.FC<HouseProviderProps> = ({ children }) => {
  const [activeHouseId, setActiveHouseIdState] = useState<number | null>(null);
  const [availableHouses, setAvailableHouses] = useState<House[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Carica la casa attiva dal localStorage all'avvio
  useEffect(() => {
    const savedHouseId = localStorage.getItem('eterna_home_active_house_id');
    if (savedHouseId) {
      const houseId = parseInt(savedHouseId, 10);
      if (!isNaN(houseId)) {
        setActiveHouseIdState(houseId);
      }
    }
  }, []);

  // Salva la casa attiva nel localStorage quando cambia
  const setActiveHouseId = (houseId: number | null) => {
    setActiveHouseIdState(houseId);
    if (houseId) {
      localStorage.setItem('eterna_home_active_house_id', houseId.toString());
    } else {
      localStorage.removeItem('eterna_home_active_house_id');
    }
  };

  // Funzione per ricaricare le case disponibili
  const refreshHouses = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/user-house/my-houses/summary', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('eterna_home_token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const houses = await response.json();
        setAvailableHouses(houses);
        
        // Se la casa attiva non è più disponibile, resetta
        if (activeHouseId && !houses.find((h: House) => h.house_id === activeHouseId)) {
          console.warn('Casa attiva non più disponibile, reset automatico');
          setActiveHouseId(null);
        }
        
        // Se non c'è una casa attiva ma ci sono case disponibili, seleziona la prima
        if (!activeHouseId && houses.length > 0) {
          setActiveHouseId(houses[0].house_id);
        }
      } else {
        console.error('Errore nel caricamento delle case:', response.status);
      }
    } catch (error) {
      console.error('Errore nel caricamento delle case:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Carica le case disponibili all'avvio
  useEffect(() => {
    refreshHouses();
  }, []);

  const value: HouseContextType = {
    activeHouseId,
    setActiveHouseId,
    availableHouses,
    setAvailableHouses,
    isLoading,
    setIsLoading,
    refreshHouses,
  };

  return (
    <HouseContext.Provider value={value}>
      {children}
    </HouseContext.Provider>
  );
};

export const useHouseContext = (): HouseContextType => {
  const context = useContext(HouseContext);
  if (context === undefined) {
    throw new Error('useHouseContext deve essere usato all\'interno di HouseProvider');
  }
  return context;
}; 