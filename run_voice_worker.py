#!/usr/bin/env python3
"""
Script per avvio del Voice Worker asincrono.
Elabora i comandi vocali dalla coda RabbitMQ.
"""
import asyncio
import logging
import sys
import os

# Aggiungi il path del progetto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workers.voice_worker import main

if __name__ == "__main__":
    # Configurazione logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('voice_worker.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Avvio Voice Worker...")
    
    try:
        # Avvia il worker
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Worker interrotto dall'utente")
    except Exception as e:
        logger.error(f"Errore avvio worker: {e}")
        sys.exit(1) 