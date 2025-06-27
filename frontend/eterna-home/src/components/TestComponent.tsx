import React from 'react';

export const TestComponent: React.FC = () => {
  return (
    <div className="p-8 bg-blue-100 rounded-lg">
      <h1 className="text-2xl font-bold text-blue-800 mb-4">
        🎉 Frontend Eterna Home Funzionante!
      </h1>
      <p className="text-blue-700">
        Il sistema frontend multi-tenant è stato configurato con successo.
      </p>
      <div className="mt-4 space-y-2">
        <div className="flex items-center space-x-2">
          <span className="w-4 h-4 bg-green-500 rounded-full"></span>
          <span>React + TypeScript</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-4 h-4 bg-green-500 rounded-full"></span>
          <span>Tailwind CSS</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-4 h-4 bg-green-500 rounded-full"></span>
          <span>Zustand State Management</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-4 h-4 bg-green-500 rounded-full"></span>
          <span>React Router</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-4 h-4 bg-green-500 rounded-full"></span>
          <span>JWT Authentication</span>
        </div>
        <div className="flex items-center space-x-2">
          <span className="w-4 h-4 bg-green-500 rounded-full"></span>
          <span>Multi-Tenant Support</span>
        </div>
      </div>
    </div>
  );
}; 