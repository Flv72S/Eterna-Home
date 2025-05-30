# 🏠 Eterna Home

A modular platform for building digital twins with NFC-based document management.

## 📋 Overview

Eterna Home is a comprehensive solution for managing building documentation through NFC tags. Each building has its own digital repository containing technical documents, floor plans, renders, system schematics, manuals, and references.

## 🚀 Features

- **NFC Tag Integration**: Quick access to building documentation through NFC scanning
- **Document Management**: Organized storage of technical documents and plans
- **Mobile App**: Flutter-based mobile application for on-site access
- **Voice Recording**: Offline voice recording with automatic transcription
- **Secure Authentication**: JWT-based authentication system

## 🛠 Tech Stack

- **Backend**: TypeScript + Express/Fastify
- **Authentication**: JWT or Clerk/Auth0
- **Storage**: S3-compatible or filesystem
- **Mobile**: Flutter
- **Transcription**: Whisper API

## 📁 Project Structure

```
/eterna-home/
│
├── api/           # REST API modules
│   ├── index.ts
│   ├── auth/      # Authentication endpoints
│   ├── repository/# Document repository endpoints
│   └── nfc/       # NFC tag management
│
├── app/           # Flutter frontend
│
├── config/        # Environment configurations
│   └── env.ts
│
├── docs/          # Technical documentation
│
├── tests/         # Unit and integration tests
│
└── scripts/       # Utility scripts
```

## 🚀 Getting Started

### Prerequisites

- Node.js (v16+)
- TypeScript
- Flutter SDK
- NFC reader/writer
- S3-compatible storage (optional)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/eterna-home.git
   cd eterna-home
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   ```bash
   cp config/env.example.ts config/env.ts
   # Edit config/env.ts with your configuration
   ```

4. Run tests:
   ```bash
   npm test
   ```

## 🧪 Testing

The project follows TDD principles. Each feature should have corresponding unit and integration tests:

```typescript
// Example test structure
describe("Feature", () => {
  it("should behave in expected way", async () => {
    // Test implementation
  });
});
```

## 📝 License

[Your License Here]

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 