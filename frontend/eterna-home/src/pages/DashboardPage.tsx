import React from 'react';
import { useAuthStore } from '../stores/authStore';
import { 
  Building2, 
  FileText, 
  Users, 
  Settings, 
  LogOut,
  Home,
  Wrench,
  Microphone,
  Cube
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user, currentTenantId, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
  };

  const menuItems = [
    {
      title: 'Dashboard',
      icon: Home,
      href: '/dashboard',
      description: 'Panoramica generale'
    },
    {
      title: 'Documenti',
      icon: FileText,
      href: '/documents',
      description: 'Gestione documenti'
    },
    {
      title: 'Utenti',
      icon: Users,
      href: '/users',
      description: 'Gestione utenti e ruoli'
    },
    {
      title: 'Modelli BIM',
      icon: Cube,
      href: '/bim',
      description: 'Gestione modelli BIM'
    },
    {
      title: 'Manutenzioni',
      icon: Wrench,
      href: '/maintenance',
      description: 'Gestione manutenzioni'
    },
    {
      title: 'Interfacce Vocali',
      icon: Microphone,
      href: '/voice',
      description: 'Comandi vocali e AI'
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
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Benvenuto, {user?.full_name || user?.username}!
            </h2>
            <p className="text-gray-600">
              Gestisci la tua casa intelligente dal pannello di controllo.
            </p>
          </div>

          {/* Menu Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {menuItems.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <item.icon className="h-8 w-8 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-lg font-medium text-gray-900">
                      {item.title}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {item.description}
                    </p>
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