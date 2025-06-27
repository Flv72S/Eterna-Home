import React from 'react';
import { useActiveHouse } from '../hooks/useActiveHouse';
import { AlertTriangle, Home } from 'lucide-react';

interface HouseRequiredGuardProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const HouseRequiredGuard: React.FC<HouseRequiredGuardProps> = ({ 
  children, 
  fallback 
}) => {
  const { hasActiveHouse, availableHouses, isLoading, selectFirstHouse } = useActiveHouse();

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Caricamento case...</span>
      </div>
    );
  }

  // No houses available
  if (availableHouses.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-center">
          <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />
          <div>
            <h3 className="text-sm font-medium text-yellow-800">
              Nessuna casa disponibile
            </h3>
            <p className="text-sm text-yellow-700 mt-1">
              Non hai case assegnate. Contatta l'amministratore per ottenere l'accesso a una casa.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // No active house but houses are available
  if (!hasActiveHouse) {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <div className="flex items-center">
          <Home className="h-5 w-5 text-blue-600 mr-2" />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-blue-800">
              Seleziona una casa
            </h3>
            <p className="text-sm text-blue-700 mt-1">
              Hai {availableHouses.length} casa{availableHouses.length > 1 ? 'e' : ''} disponibile{availableHouses.length > 1 ? 'i' : ''}. 
              Seleziona una casa per continuare.
            </p>
          </div>
          <button
            onClick={selectFirstHouse}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors text-sm"
          >
            Seleziona prima casa
          </button>
        </div>
      </div>
    );
  }

  // Custom fallback
  if (fallback) {
    return <>{fallback}</>;
  }

  // Render children if house is active
  return <>{children}</>;
};

export default HouseRequiredGuard; 