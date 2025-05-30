import { z } from 'zod';
import dotenv from 'dotenv';

// Carica le variabili d'ambiente
dotenv.config();

// Schema di validazione per le variabili d'ambiente
const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.string().default('3000'),
  
  // Database
  MONGODB_URI: z.string(),
  
  // JWT
  JWT_SECRET: z.string(),
  JWT_EXPIRES_IN: z.string().default('7d'),
  
  // Storage
  STORAGE_TYPE: z.enum(['s3', 'local']).default('local'),
  S3_BUCKET: z.string().optional(),
  S3_REGION: z.string().optional(),
  S3_ACCESS_KEY: z.string().optional(),
  S3_SECRET_KEY: z.string().optional(),
  
  // Whisper API
  WHISPER_API_KEY: z.string().optional(),
});

// Valida e esporta la configurazione
const config = envSchema.parse(process.env);

export default config; 