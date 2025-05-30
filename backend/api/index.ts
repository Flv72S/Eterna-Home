import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import config from '../core/config';

// Importa i router
import repositoryRouter from './routes/repository';
import authRouter from './routes/auth';
import nfcRouter from './routes/nfc';

const app = express();

// Middleware
app.use(cors());
app.use(helmet());
app.use(morgan('dev'));
app.use(express.json());

// Routes
app.use('/api/repository', repositoryRouter);
app.use('/api/auth', authRouter);
app.use('/api/nfc', nfcRouter);

// Error handling
app.use((err: Error, req: express.Request, res: express.Response, next: express.NextFunction) => {
  console.error(err.stack);
  res.status(500).json({
    error: 'Errore interno del server',
    message: process.env.NODE_ENV === 'development' ? err.message : undefined
  });
});

// Avvia il server
const PORT = config.PORT;
app.listen(PORT, () => {
  console.log(`Server in esecuzione sulla porta ${PORT}`);
});

export default app; 