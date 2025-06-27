# Eterna Home Frontend

Frontend React per il sistema di gestione multi-tenant Eterna Home.

## 🚀 Tecnologie Utilizzate

- **React 18** con TypeScript
- **Vite** per build e development
- **Tailwind CSS** per styling
- **React Router** per routing
- **Zustand** per state management
- **Axios** per chiamate API
- **JWT** per autenticazione

## 📦 Installazione

```bash
# Installa le dipendenze
npm install

# Avvia il server di sviluppo
npm run dev

# Build per produzione
npm run build

# Preview build di produzione
npm run preview
```

## 🔧 Configurazione

Il frontend è configurato per connettersi al backend su `http://localhost:8000` tramite proxy Vite.

### Variabili d'ambiente

Crea un file `.env.local` nella root del progetto:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Eterna Home
```

## 🏗️ Struttura del Progetto

```
src/
├── components/          # Componenti riutilizzabili
│   ├── AuthGuard.tsx   # Protezione route
│   ├── LoginForm.tsx   # Form di login
│   └── TenantSelector.tsx # Selezione tenant
├── pages/              # Pagine dell'applicazione
│   ├── LoginPage.tsx   # Pagina login
│   └── DashboardPage.tsx # Dashboard principale
├── stores/             # State management (Zustand)
│   └── authStore.ts    # Store autenticazione
├── services/           # Servizi API
│   └── authService.ts  # Servizio autenticazione
├── types/              # Definizioni TypeScript
│   ├── auth.ts         # Tipi autenticazione
│   └── api.ts          # Tipi API
├── utils/              # Utility functions
├── hooks/              # Custom hooks
├── App.tsx             # Componente principale
├── main.tsx            # Entry point
└── index.css           # Stili globali
```

## 🔐 Autenticazione Multi-Tenant

Il sistema supporta autenticazione JWT con isolamento multi-tenant:

1. **Login**: L'utente effettua login con email/password
2. **Token JWT**: Il backend restituisce un token con `tenant_id`, `user_id`, `role`
3. **Selezione Tenant**: Se l'utente ha accesso a più tenant, può selezionarne uno
4. **Isolamento**: Tutte le operazioni successive sono filtrate per il tenant selezionato

### Flusso di Autenticazione

```typescript
// Login
const { login } = useAuthStore();
await login({ email: 'user@example.com', password: 'password' });

// Verifica autenticazione
const { isAuthenticated, currentTenantId } = useAuthStore();

// Logout
const { logout } = useAuthStore();
logout();
```

## 🛣️ Routing

- `/login` - Pagina di login
- `/select-tenant` - Selezione tenant (se multi-tenant)
- `/dashboard` - Dashboard principale (protetta)
- `/*` - Redirect a `/dashboard`

### Protezione Route

```typescript
<AuthGuard>
  <ProtectedComponent />
</AuthGuard>
```

## 🎨 UI Components

Il progetto utilizza Tailwind CSS con componenti personalizzati:

- **Form di Login**: Design moderno con validazione
- **Dashboard**: Layout responsive con menu a griglia
- **Tenant Selector**: Selezione tenant con UI intuitiva
- **AuthGuard**: Protezione automatica delle route

## 🔄 State Management

Zustand è utilizzato per la gestione dello stato globale:

```typescript
// Store autenticazione
const authStore = useAuthStore();

// Accesso allo stato
const { user, isAuthenticated, currentTenantId } = authStore;

// Azioni
const { login, logout, setCurrentTenant } = authStore;
```

## 🌐 API Integration

Axios è configurato con interceptors per:

- Aggiunta automatica del token JWT
- Gestione errori 401/403 (logout automatico)
- Proxy per sviluppo locale

```typescript
// Chiamata API con autenticazione automatica
const response = await authService.login(credentials);
```

## 🧪 Testing

```bash
# Test unitari
npm test

# Test e2e
npm run test:e2e
```

## 📱 Responsive Design

Il frontend è completamente responsive e supporta:

- Desktop (1024px+)
- Tablet (768px - 1023px)
- Mobile (< 768px)

## 🔒 Sicurezza

- **JWT Storage**: Token salvati in localStorage con persistenza
- **Route Protection**: Tutte le route private protette da AuthGuard
- **Tenant Isolation**: Isolamento completo tra tenant
- **Auto Logout**: Logout automatico su token scaduto

## 🚀 Deployment

```bash
# Build per produzione
npm run build

# I file di build sono in /dist
```

## 📝 TODO

- [ ] Implementare pagine per documenti, utenti, BIM
- [ ] Aggiungere gestione errori avanzata
- [ ] Implementare notifiche push
- [ ] Aggiungere tema scuro
- [ ] Implementare PWA
- [ ] Aggiungere test unitari completi 