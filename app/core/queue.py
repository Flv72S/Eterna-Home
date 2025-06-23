"""
Configurazione e gestione della coda messaggi RabbitMQ per elaborazione asincrona.
"""
import json
import logging
from typing import Dict, Any, Optional
import aio_pika
from aio_pika import connect_robust, Message, DeliveryMode
from app.core.config import settings

logger = logging.getLogger(__name__)

class RabbitMQManager:
    """Gestore per la connessione e operazioni RabbitMQ."""
    
    def __init__(self):
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.queue: Optional[aio_pika.Queue] = None
        self.exchange: Optional[aio_pika.Exchange] = None
        
    async def connect(self) -> None:
        """Stabilisce la connessione a RabbitMQ."""
        try:
            # Configurazione RabbitMQ (default per sviluppo)
            rabbitmq_url = getattr(settings, 'RABBITMQ_URL', 'amqp://guest:guest@localhost:5672/')
            
            logger.info(f"Connessione a RabbitMQ: {rabbitmq_url}")
            self.connection = await connect_robust(rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Dichiarazione exchange
            self.exchange = await self.channel.declare_exchange(
                "voice_commands",
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )
            
            # Dichiarazione coda
            self.queue = await self.channel.declare_queue(
                "voice_commands_queue",
                durable=True
            )
            
            # Binding coda all'exchange
            await self.queue.bind(self.exchange, "voice.command")
            
            logger.info("Connessione RabbitMQ stabilita con successo")
            
        except Exception as e:
            logger.error(f"Errore connessione RabbitMQ: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Chiude la connessione RabbitMQ."""
        if self.connection:
            await self.connection.close()
            logger.info("Connessione RabbitMQ chiusa")
    
    async def publish_message(self, message_data: Dict[str, Any], routing_key: str = "voice.command") -> None:
        """Pubblica un messaggio nella coda."""
        if not self.channel or not self.exchange:
            raise RuntimeError("RabbitMQ non connesso")
        
        try:
            # Serializzazione messaggio
            message_body = json.dumps(message_data, default=str).encode()
            
            # Creazione messaggio
            message = Message(
                body=message_body,
                delivery_mode=DeliveryMode.PERSISTENT,
                content_type="application/json"
            )
            
            # Pubblicazione
            await self.exchange.publish(message, routing_key=routing_key)
            logger.info(f"Messaggio pubblicato con routing_key: {routing_key}")
            
        except Exception as e:
            logger.error(f"Errore pubblicazione messaggio: {e}")
            raise
    
    async def consume_messages(self, callback) -> None:
        """Consuma messaggi dalla coda."""
        if not self.queue:
            raise RuntimeError("Coda RabbitMQ non inizializzata")
        
        try:
            async with self.queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        try:
                            # Parsing messaggio
                            message_data = json.loads(message.body.decode())
                            logger.info(f"Messaggio ricevuto: {message_data}")
                            
                            # Esecuzione callback
                            await callback(message_data)
                            
                        except Exception as e:
                            logger.error(f"Errore elaborazione messaggio: {e}")
                            
        except Exception as e:
            logger.error(f"Errore consumo messaggi: {e}")
            raise

# Istanza globale del manager
rabbitmq_manager = RabbitMQManager()

async def get_rabbitmq_manager() -> RabbitMQManager:
    """Restituisce l'istanza del manager RabbitMQ."""
    return rabbitmq_manager 