import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../stores/authStore';
import { Building2, Check } from 'lucide-react';

export const TenantSelector: React.FC = () => {
  const navigate = useNavigate();
  const { availableTenants, currentTenantId, setCurrentTenant, user } = useAuthStore();

  const handleTenantSelect = (tenantId: string) => {
    setCurrentTenant(tenantId);
    navigate('/dashboard');
  };

  // If only one tenant available, auto-select it
  React.useEffect(() => {
    if (availableTenants.length === 1 && !currentTenantId) {
      handleTenantSelect(availableTenants[0]);
    }
  }, [availableTenants, currentTenantId]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-blue-100">
            <Building2 className="h-6 w-6 text-blue-600" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Seleziona il Tenant
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Scegli l'organizzazione con cui vuoi lavorare
          </p>
        </div>

        <div className="space-y-4">
          {availableTenants.map((tenantId) => (
            <button
              key={tenantId}
              onClick={() => handleTenantSelect(tenantId)}
              className="w-full flex items-center justify-between p-4 border border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors"
            >
              <div className="flex items-center">
                <Building2 className="h-5 w-5 text-gray-400 mr-3" />
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    Tenant {tenantId.slice(0, 8)}...
                  </p>
                  <p className="text-xs text-gray-500">
                    {user?.email}
                  </p>
                </div>
              </div>
              {currentTenantId === tenantId && (
                <Check className="h-5 w-5 text-blue-600" />
              )}
            </button>
          ))}
        </div>

        <div className="text-center">
          <p className="text-xs text-gray-500">
            Selezionando un tenant, accedi al sistema di gestione associato
          </p>
        </div>
      </div>
    </div>
  );
}; 