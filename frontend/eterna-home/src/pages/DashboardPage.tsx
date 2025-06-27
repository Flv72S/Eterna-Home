import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../stores/authStore';
import { useActiveHouse } from '../hooks/useActiveHouse';
import HouseSelector from '../components/HouseSelector';
import { apiService } from '../services/apiService';
import { 
  Building2, 
  FileText, 
  Users, 
  Settings, 
  LogOut,
  Home,
  Wrench,
  Mic,
  Box,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';

interface DashboardStats {
  documents: number;
  bimModels: number;
  nodes: number;
  maintenanceTasks: number;
}

export const DashboardPage: React.FC = () => {
  const { user, currentTenantId, logout } = useAuthStore();
  const { 
    activeHouse, 
    hasActiveHouse, 
    isLoading: housesLoading 
  } = useActiveHouse();
  
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(false);

  const handleLogout = () => {
    logout();
  };

  // Carica statistiche per la casa attiva
  const loadDashboardStats = async () => {
    if (!hasActiveHouse) return;
    
    setLoading(true);
    try {
      const [documentsRes, bimRes, nodesRes] = await Promise.all([
        apiService.getDocuments({ limit: 1 }),
        apiService.getBimModels({ limit: 1 }),
        apiService.getNodes({ limit: 1 })
      ]);

      setStats({
        documents: (documentsRes as any).total || 0,
        bimModels: (bimRes as any).total || 0,
        nodes: (nodesRes as any).total || 0,
        maintenanceTasks: 0 // TODO: implementare quando disponibile
      });
    } catch (error) {
      console.error('Errore nel caricamento statistiche:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (hasActiveHouse) {
      loadDashboardStats();
    }
  }, [hasActiveHouse, activeHouse?.house_id]);

  const menuItems = [
    {
      title: 'Dashboard',
      icon: Home,
      href: '/dashboard',
      description: 'Panoramica generale',
      disabled: !hasActiveHouse
    },
    {
      title: 'Documenti',
      icon: FileText,
      href: '/documents',
      description: 'Gestione documenti',
      disabled: !hasActiveHouse
    },
    {
      title: 'Utenti',
      icon: Users,
      href: '/users',
      description: 'Gestione utenti e ruoli'
    },
    {
      title: 'Modelli BIM',
      icon: Box,
      href: '/bim',
      description: 'Gestione modelli BIM',
      disabled: !hasActiveHouse
    },
    {
      title: 'Manutenzioni',
      icon: Wrench,
      href: '/maintenance',
      description: 'Gestione manutenzioni',
      disabled: !hasActiveHouse
    },
    {
      title: 'Interfacce Vocali',
      icon: Mic,
      href: '/voice',
      description: 'Comandi vocali e AI',
      disabled: !hasActiveHouse
    },
    {
      title: 'Impostazioni',
      icon: Settings,
      href: '/settings',
      description: 'Configurazione sistema'
    }
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Building2 className="h-8 w-8 text-blue-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">
                Eterna Home
              </h1>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* House Selector */}
              <div className="w-64">
                <HouseSelector />
              </div>
              
              <div className="text-sm text-gray-500">
                <span className="font-medium">{user?.email}</span>
                <span className="mx-2">•</span>
                <span>Tenant: {currentTenantId?.slice(0, 8)}...</span>
              </div>
              
              <button
                onClick={handleLogout}
                className="flex items-center text-sm text-gray-500 hover:text-gray-700"
              >
                <LogOut className="h-4 w-4 mr-1" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Welcome Section */}
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Benvenuto, {user?.full_name || user?.username}!
                </h2>
                <p className="text-gray-600">
                  {hasActiveHouse 
                    ? `Gestisci la casa "${activeHouse?.house_name}" dal pannello di controllo.`
                    : 'Seleziona una casa per iniziare a gestire la tua casa intelligente.'
                  }
                </p>
              </div>
              
              {hasActiveHouse && (
                <div className="flex items-center space-x-2 text-green-600">
                  <CheckCircle className="h-5 w-5" />
                  <span className="text-sm font-medium">Casa attiva</span>
                </div>
              )}
            </div>
          </div>

          {/* House Selection Warning */}
          {!hasActiveHouse && !housesLoading && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <div className="flex items-center">
                <AlertTriangle className="h-5 w-5 text-yellow-600 mr-2" />
                <div>
                  <h3 className="text-sm font-medium text-yellow-800">
                    Nessuna casa selezionata
                  </h3>
                  <p className="text-sm text-yellow-700 mt-1">
                    Seleziona una casa dall'elenco sopra per accedere alle funzionalità di gestione.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Dashboard Stats */}
          {hasActiveHouse && stats && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <FileText className="h-8 w-8 text-blue-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Documenti</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {loading ? '...' : stats.documents}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <Box className="h-8 w-8 text-green-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Modelli BIM</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {loading ? '...' : stats.bimModels}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <Home className="h-8 w-8 text-purple-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Nodi IoT</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {loading ? '...' : stats.nodes}
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center">
                  <Wrench className="h-8 w-8 text-orange-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Manutenzioni</p>
                    <p className="text-2xl font-semibold text-gray-900">
                      {loading ? '...' : stats.maintenanceTasks}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Menu Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {menuItems.map((item) => (
              <a
                key={item.href}
                href={item.disabled ? '#' : item.href}
                className={`
                  bg-white rounded-lg shadow p-6 transition-all
                  ${item.disabled 
                    ? 'opacity-50 cursor-not-allowed' 
                    : 'hover:shadow-md cursor-pointer'
                  }
                `}
                onClick={item.disabled ? (e) => e.preventDefault() : undefined}
              >
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <item.icon className={`h-8 w-8 ${item.disabled ? 'text-gray-400' : 'text-blue-600'}`} />
                  </div>
                  <div className="ml-4">
                    <h3 className={`text-lg font-medium ${item.disabled ? 'text-gray-400' : 'text-gray-900'}`}>
                      {item.title}
                    </h3>
                    <p className={`text-sm ${item.disabled ? 'text-gray-400' : 'text-gray-500'}`}>
                      {item.description}
                    </p>
                    {item.disabled && (
                      <p className="text-xs text-yellow-600 mt-1">
                        Seleziona una casa per accedere
                      </p>
                    )}
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}; 