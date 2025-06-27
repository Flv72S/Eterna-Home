import { useHouseContext } from '../context/HouseContext';

/**
 * Hook personalizzato per accedere rapidamente alla casa attiva
 * e alle funzioni correlate
 */
export const useActiveHouse = () => {
  const { 
    activeHouseId, 
    setActiveHouseId, 
    availableHouses, 
    isLoading,
    refreshHouses 
  } = useHouseContext();

  const activeHouse = availableHouses.find(house => house.house_id === activeHouseId);

  const hasActiveHouse = activeHouseId !== null;
  
  const hasMultipleHouses = availableHouses.length > 1;
  
  const isOwner = activeHouse?.is_owner || false;
  
  const roleInHouse = activeHouse?.role_in_house || 'Utente';

  return {
    // Valori
    activeHouseId,
    activeHouse,
    availableHouses,
    isLoading,
    
    // Funzioni
    setActiveHouseId,
    refreshHouses,
    
    // Computed values
    hasActiveHouse,
    hasMultipleHouses,
    isOwner,
    roleInHouse,
    
    // Utility functions
    selectFirstHouse: () => {
      if (availableHouses.length > 0 && !activeHouseId) {
        setActiveHouseId(availableHouses[0].house_id);
      }
    },
    
    clearActiveHouse: () => {
      setActiveHouseId(null);
    },
    
    // Verifica se una casa specifica è attiva
    isActiveHouse: (houseId: number) => activeHouseId === houseId,
    
    // Ottieni casa per ID
    getHouseById: (houseId: number) => 
      availableHouses.find(house => house.house_id === houseId),
    
    // Ottieni case di proprietà
    getOwnedHouses: () => availableHouses.filter(house => house.is_owner),
    
    // Ottieni case in cui è residente
    getResidentHouses: () => availableHouses.filter(house => !house.is_owner),
  };
}; 