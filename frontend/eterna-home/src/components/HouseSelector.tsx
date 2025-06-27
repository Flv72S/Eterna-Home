import React, { useState } from 'react';
import { useHouseContext } from '../context/HouseContext';
import { ChevronDown, Home, AlertCircle } from 'lucide-react';

interface HouseSelectorProps {
  className?: string;
}

export const HouseSelector: React.FC<HouseSelectorProps> = ({ className = '' }) => {
  const { 
    activeHouseId, 
    setActiveHouseId, 
    availableHouses, 
    isLoading 
  } = useHouseContext();
  
  const [isOpen, setIsOpen] = useState(false);

  const activeHouse = availableHouses.find(house => house.house_id === activeHouseId);

  const handleHouseSelect = (houseId: number) => {
    setActiveHouseId(houseId);
    setIsOpen(false);
  };

  const handleToggle = () => {
    if (!isLoading && availableHouses.length > 0) {
      setIsOpen(!isOpen);
    }
  };

  if (isLoading) {
    return (
      <div className={`flex items-center space-x-2 px-3 py-2 bg-gray-100 rounded-lg ${className}`}>
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
        <span className="text-sm text-gray-600">Caricamento case...</span>
      </div>
    );
  }

  if (availableHouses.length === 0) {
    return (
      <div className={`flex items-center space-x-2 px-3 py-2 bg-yellow-50 border border-yellow-200 rounded-lg ${className}`}>
        <AlertCircle className="h-4 w-4 text-yellow-600" />
        <span className="text-sm text-yellow-800">Nessuna casa disponibile</span>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {/* Dropdown Trigger */}
      <button
        onClick={handleToggle}
        className={`
          flex items-center justify-between w-full px-3 py-2 
          bg-white border border-gray-300 rounded-lg shadow-sm
          hover:bg-gray-50 focus:outline-none focus:ring-2 
          focus:ring-blue-500 focus:border-blue-500
          transition-colors duration-200
          ${isOpen ? 'ring-2 ring-blue-500 border-blue-500' : ''}
        `}
        disabled={isLoading}
      >
        <div className="flex items-center space-x-2">
          <Home className="h-4 w-4 text-gray-500" />
          <div className="text-left">
            <div className="text-sm font-medium text-gray-900">
              {activeHouse ? activeHouse.house_name : 'Seleziona casa'}
            </div>
            {activeHouse && (
              <div className="text-xs text-gray-500">
                {activeHouse.house_address}
              </div>
            )}
          </div>
        </div>
        <ChevronDown 
          className={`h-4 w-4 text-gray-400 transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`} 
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-300 rounded-lg shadow-lg z-50 max-h-60 overflow-y-auto">
          {availableHouses.map((house) => (
            <button
              key={house.house_id}
              onClick={() => handleHouseSelect(house.house_id)}
              className={`
                w-full px-3 py-2 text-left hover:bg-gray-50 
                transition-colors duration-150
                ${house.house_id === activeHouseId ? 'bg-blue-50 border-l-4 border-blue-500' : ''}
                ${!house.is_active ? 'opacity-50 cursor-not-allowed' : ''}
              `}
              disabled={!house.is_active}
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-gray-900">
                    {house.house_name}
                  </div>
                  <div className="text-xs text-gray-500">
                    {house.house_address}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    {house.is_owner ? 'Proprietario' : house.role_in_house || 'Utente'}
                  </div>
                </div>
                {house.house_id === activeHouseId && (
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Overlay per chiudere il dropdown */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default HouseSelector; 