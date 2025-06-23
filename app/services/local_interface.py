"""
Servizio per interfacce locali e integrazione tra comandi vocali e altre aree del sistema.
Gestisce la connessione tra comandi vocali, IoT, BIM, documenti e altre funzionalità.
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlmodel import Session, select

from app.core.config import settings
from app.models.audio_log import AudioLog
from app.models.node import Node
from app.models.house import House
from app.models.bim_model import BIMModel
from app.models.document import Document
from app.models.maintenance import MaintenanceRecord
from app.models.booking import Booking
from app.services.speech_to_text import SpeechToTextService
from app.services.audio_log import AudioLogService
from app.db.session import get_session

logger = logging.getLogger(__name__)

class LocalInterfaceService:
    """Servizio per interfacce locali e integrazione sistema."""
    
    def __init__(self):
        self.speech_service = SpeechToTextService()
        self.audio_service = AudioLogService()
        
    async def process_voice_command(self, audio_log_id: int) -> Dict[str, Any]:
        """
        Processa un comando vocale e lo integra con le altre aree del sistema.
        
        Args:
            audio_log_id: ID dell'AudioLog da processare
            
        Returns:
            Dict con risultato elaborazione e azioni eseguite
        """
        try:
            logger.info(f"Processamento comando vocale: {audio_log_id}")
            
            db = next(get_session())
            audio_log = db.get(AudioLog, audio_log_id)
            
            if not audio_log:
                raise Exception(f"AudioLog {audio_log_id} non trovato")
            
            # Ottieni testo trascritto
            text = audio_log.transcribed_text
            if not text:
                raise Exception("Nessun testo trascritto disponibile")
            
            # Analizza comando e determina azioni
            actions = await self._analyze_command(text, audio_log, db)
            
            # Esegui azioni
            results = await self._execute_actions(actions, audio_log, db)
            
            # Aggiorna risposta
            response_text = self._generate_response(results)
            audio_log.response_text = response_text
            audio_log.processing_status = "completed"
            db.commit()
            
            logger.info(f"Comando vocale processato: {len(actions)} azioni eseguite")
            
            return {
                "success": True,
                "audio_log_id": audio_log_id,
                "actions_executed": len(actions),
                "results": results,
                "response": response_text
            }
            
        except Exception as e:
            logger.error(f"Errore processamento comando vocale: {e}")
            raise
    
    async def _analyze_command(self, text: str, audio_log: AudioLog, db: Session) -> List[Dict[str, Any]]:
        """Analizza il comando vocale e determina le azioni da eseguire."""
        text_lower = text.lower()
        actions = []
        
        # Comandi IoT - Controllo nodi
        if any(word in text_lower for word in ["accendi", "spegni", "luci", "luce"]):
            actions.extend(await self._analyze_iot_commands(text_lower, audio_log, db))
        
        # Comandi BIM - Gestione modelli
        if any(word in text_lower for word in ["bim", "modello", "converti", "carica"]):
            actions.extend(await self._analyze_bim_commands(text_lower, audio_log, db))
        
        # Comandi documenti - Gestione file
        if any(word in text_lower for word in ["documento", "file", "carica", "scarica"]):
            actions.extend(await self._analyze_document_commands(text_lower, audio_log, db))
        
        # Comandi manutenzione - Gestione manutenzioni
        if any(word in text_lower for word in ["manutenzione", "ripara", "controlla", "stato"]):
            actions.extend(await self._analyze_maintenance_commands(text_lower, audio_log, db))
        
        # Comandi prenotazioni - Gestione booking
        if any(word in text_lower for word in ["prenota", "prenotazione", "stanza", "camera"]):
            actions.extend(await self._analyze_booking_commands(text_lower, audio_log, db))
        
        # Comandi informativi - Query sistema
        if any(word in text_lower for word in ["stato", "temperatura", "umidità", "informazioni"]):
            actions.extend(await self._analyze_info_commands(text_lower, audio_log, db))
        
        # Comando di aiuto
        if any(word in text_lower for word in ["aiuto", "help", "comandi"]):
            actions.append({
                "type": "help",
                "description": "Mostra comandi disponibili"
            })
        
        return actions
    
    async def _analyze_iot_commands(self, text: str, audio_log: AudioLog, db: Session) -> List[Dict[str, Any]]:
        """Analizza comandi IoT."""
        actions = []
        
        # Trova nodi nella casa dell'utente
        nodes_query = select(Node).where(
            Node.house_id == audio_log.house_id,
            Node.user_id == audio_log.user_id
        )
        nodes = db.exec(nodes_query).all()
        
        if "accendi" in text and "luci" in text:
            for node in nodes:
                if "luce" in node.name.lower() or "light" in node.name.lower():
                    actions.append({
                        "type": "iot_control",
                        "action": "turn_on",
                        "node_id": node.id,
                        "node_name": node.name,
                        "description": f"Accende {node.name}"
                    })
        
        elif "spegni" in text and "luci" in text:
            for node in nodes:
                if "luce" in node.name.lower() or "light" in node.name.lower():
                    actions.append({
                        "type": "iot_control",
                        "action": "turn_off",
                        "node_id": node.id,
                        "node_name": node.name,
                        "description": f"Spegne {node.name}"
                    })
        
        return actions
    
    async def _analyze_bim_commands(self, text: str, audio_log: AudioLog, db: Session) -> List[Dict[str, Any]]:
        """Analizza comandi BIM."""
        actions = []
        
        if "converti" in text and "bim" in text:
            # Trova modelli BIM dell'utente
            bim_models_query = select(BIMModel).where(
                BIMModel.user_id == audio_log.user_id,
                BIMModel.conversion_status == "pending"
            )
            bim_models = db.exec(bim_models_query).all()
            
            for model in bim_models:
                actions.append({
                    "type": "bim_conversion",
                    "action": "convert",
                    "model_id": model.id,
                    "model_name": model.name,
                    "description": f"Converte modello BIM {model.name}"
                })
        
        elif "stato" in text and "bim" in text:
            actions.append({
                "type": "bim_status",
                "action": "check_status",
                "user_id": audio_log.user_id,
                "description": "Controlla stato modelli BIM"
            })
        
        return actions
    
    async def _analyze_document_commands(self, text: str, audio_log: AudioLog, db: Session) -> List[Dict[str, Any]]:
        """Analizza comandi documenti."""
        actions = []
        
        if "lista" in text and "documenti" in text:
            actions.append({
                "type": "document_list",
                "action": "list",
                "user_id": audio_log.user_id,
                "description": "Lista documenti disponibili"
            })
        
        elif "cerca" in text and "documento" in text:
            actions.append({
                "type": "document_search",
                "action": "search",
                "query": text,
                "user_id": audio_log.user_id,
                "description": f"Cerca documenti con: {text}"
            })
        
        return actions
    
    async def _analyze_maintenance_commands(self, text: str, audio_log: AudioLog, db: Session) -> List[Dict[str, Any]]:
        """Analizza comandi manutenzione."""
        actions = []
        
        if "stato" in text and "manutenzione" in text:
            actions.append({
                "type": "maintenance_status",
                "action": "check_status",
                "user_id": audio_log.user_id,
                "description": "Controlla stato manutenzioni"
            })
        
        elif "nuova" in text and "manutenzione" in text:
            actions.append({
                "type": "maintenance_create",
                "action": "create",
                "user_id": audio_log.user_id,
                "description": "Crea nuova manutenzione"
            })
        
        return actions
    
    async def _analyze_booking_commands(self, text: str, audio_log: AudioLog, db: Session) -> List[Dict[str, Any]]:
        """Analizza comandi prenotazioni."""
        actions = []
        
        if "prenota" in text and "stanza" in text:
            actions.append({
                "type": "booking_create",
                "action": "create",
                "user_id": audio_log.user_id,
                "description": "Crea nuova prenotazione stanza"
            })
        
        elif "prenotazioni" in text:
            actions.append({
                "type": "booking_list",
                "action": "list",
                "user_id": audio_log.user_id,
                "description": "Lista prenotazioni"
            })
        
        return actions
    
    async def _analyze_info_commands(self, text: str, audio_log: AudioLog, db: Session) -> List[Dict[str, Any]]:
        """Analizza comandi informativi."""
        actions = []
        
        if "temperatura" in text:
            actions.append({
                "type": "sensor_read",
                "action": "temperature",
                "house_id": audio_log.house_id,
                "description": "Legge temperatura casa"
            })
        
        elif "umidità" in text:
            actions.append({
                "type": "sensor_read",
                "action": "humidity",
                "house_id": audio_log.house_id,
                "description": "Legge umidità casa"
            })
        
        elif "stato" in text and "sistema" in text:
            actions.append({
                "type": "system_status",
                "action": "overview",
                "house_id": audio_log.house_id,
                "description": "Stato generale sistema"
            })
        
        return actions
    
    async def _execute_actions(self, actions: List[Dict[str, Any]], audio_log: AudioLog, db: Session) -> List[Dict[str, Any]]:
        """Esegue le azioni determinate dall'analisi del comando."""
        results = []
        
        for action in actions:
            try:
                result = await self._execute_single_action(action, audio_log, db)
                results.append({
                    "action": action,
                    "success": True,
                    "result": result
                })
            except Exception as e:
                logger.error(f"Errore esecuzione azione {action['type']}: {e}")
                results.append({
                    "action": action,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    async def _execute_single_action(self, action: Dict[str, Any], audio_log: AudioLog, db: Session) -> Any:
        """Esegue una singola azione."""
        action_type = action.get("type")
        
        if action_type == "iot_control":
            return await self._execute_iot_control(action, db)
        elif action_type == "bim_conversion":
            return await self._execute_bim_conversion(action, db)
        elif action_type == "document_list":
            return await self._execute_document_list(action, db)
        elif action_type == "maintenance_status":
            return await self._execute_maintenance_status(action, db)
        elif action_type == "booking_list":
            return await self._execute_booking_list(action, db)
        elif action_type == "sensor_read":
            return await self._execute_sensor_read(action, db)
        elif action_type == "system_status":
            return await self._execute_system_status(action, db)
        elif action_type == "help":
            return self._execute_help()
        else:
            raise Exception(f"Tipo azione non supportato: {action_type}")
    
    async def _execute_iot_control(self, action: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Esegue controllo IoT."""
        node_id = action.get("node_id")
        action_type = action.get("action")
        
        # Simula controllo IoT (in produzione si integrerebbe con protocolli reali)
        await asyncio.sleep(1)
        
        return {
            "node_id": node_id,
            "action": action_type,
            "status": "executed",
            "message": f"Nodo {node_id} {action_type} eseguito"
        }
    
    async def _execute_bim_conversion(self, action: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Esegue conversione BIM."""
        model_id = action.get("model_id")
        
        # Avvia conversione BIM asincrona
        from app.workers.conversion_worker import process_bim_model
        task = process_bim_model.delay(model_id, "auto")
        
        return {
            "model_id": model_id,
            "task_id": task.id,
            "status": "started",
            "message": f"Conversione BIM {model_id} avviata"
        }
    
    async def _execute_document_list(self, action: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Esegue lista documenti."""
        user_id = action.get("user_id")
        
        documents_query = select(Document).where(Document.user_id == user_id).limit(10)
        documents = db.exec(documents_query).all()
        
        return {
            "count": len(documents),
            "documents": [{"id": d.id, "name": d.name} for d in documents]
        }
    
    async def _execute_maintenance_status(self, action: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Esegue controllo stato manutenzioni."""
        user_id = action.get("user_id")
        
        maintenance_query = select(MaintenanceRecord).where(
            MaintenanceRecord.user_id == user_id
        ).limit(5)
        maintenance_records = db.exec(maintenance_query).all()
        
        return {
            "count": len(maintenance_records),
            "pending": len([m for m in maintenance_records if m.status == "pending"]),
            "in_progress": len([m for m in maintenance_records if m.status == "in_progress"])
        }
    
    async def _execute_booking_list(self, action: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Esegue lista prenotazioni."""
        user_id = action.get("user_id")
        
        bookings_query = select(Booking).where(Booking.user_id == user_id).limit(5)
        bookings = db.exec(bookings_query).all()
        
        return {
            "count": len(bookings),
            "bookings": [{"id": b.id, "room_id": b.room_id, "start_date": b.start_date} for b in bookings]
        }
    
    async def _execute_sensor_read(self, action: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Esegue lettura sensori."""
        sensor_type = action.get("action")
        house_id = action.get("house_id")
        
        # Simula lettura sensori (in produzione si integrerebbe con sensori reali)
        await asyncio.sleep(0.5)
        
        if sensor_type == "temperature":
            return {"temperature": 22.5, "unit": "°C", "timestamp": datetime.now().isoformat()}
        elif sensor_type == "humidity":
            return {"humidity": 45.2, "unit": "%", "timestamp": datetime.now().isoformat()}
        else:
            return {"error": "Tipo sensore non supportato"}
    
    async def _execute_system_status(self, action: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Esegue controllo stato sistema."""
        house_id = action.get("house_id")
        
        # Conta nodi attivi
        nodes_query = select(Node).where(Node.house_id == house_id, Node.is_active == True)
        active_nodes = db.exec(nodes_query).all()
        
        # Conta manutenzioni pendenti
        maintenance_query = select(MaintenanceRecord).where(
            MaintenanceRecord.house_id == house_id,
            MaintenanceRecord.status == "pending"
        )
        pending_maintenance = db.exec(maintenance_query).all()
        
        return {
            "active_nodes": len(active_nodes),
            "pending_maintenance": len(pending_maintenance),
            "system_status": "operational",
            "timestamp": datetime.now().isoformat()
        }
    
    def _execute_help(self) -> Dict[str, Any]:
        """Esegue comando di aiuto."""
        return {
            "commands": [
                "Accendi/spegni luci - Controllo illuminazione",
                "Stato temperatura/umidità - Lettura sensori",
                "Converti BIM - Conversione modelli BIM",
                "Lista documenti - Visualizza documenti",
                "Stato manutenzione - Controlla manutenzioni",
                "Prenota stanza - Gestione prenotazioni",
                "Stato sistema - Panoramica sistema"
            ]
        }
    
    def _generate_response(self, results: List[Dict[str, Any]]) -> str:
        """Genera risposta testuale basata sui risultati delle azioni."""
        if not results:
            return "Nessuna azione eseguita. Prova a riformulare il comando."
        
        response_parts = []
        
        for result in results:
            if result["success"]:
                action = result["action"]
                action_type = action.get("type")
                
                if action_type == "iot_control":
                    response_parts.append(f"{action['description']} completato.")
                elif action_type == "bim_conversion":
                    response_parts.append(f"{action['description']} avviata.")
                elif action_type == "sensor_read":
                    data = result["result"]
                    if "temperature" in data:
                        response_parts.append(f"Temperatura: {data['temperature']}{data['unit']}")
                    elif "humidity" in data:
                        response_parts.append(f"Umidità: {data['humidity']}{data['unit']}")
                elif action_type == "help":
                    commands = result["result"]["commands"]
                    response_parts.append("Comandi disponibili: " + ", ".join(commands[:3]) + "...")
                else:
                    response_parts.append(f"{action['description']} completato.")
            else:
                response_parts.append(f"Errore: {result['error']}")
        
        return " ".join(response_parts)
    
    async def get_interface_status(self) -> Dict[str, Any]:
        """Restituisce lo stato delle interfacce locali."""
        return {
            "local_interfaces_enabled": settings.ENABLE_LOCAL_INTERFACES,
            "voice_commands_enabled": settings.ENABLE_VOICE_COMMANDS,
            "speech_service_status": self.speech_service.get_service_status(),
            "integrations": {
                "iot": settings.ENABLE_IOT_INTEGRATION,
                "bim": settings.ENABLE_BIM_INTEGRATION,
                "documents": settings.ENABLE_DOCUMENT_INTEGRATION
            }
        } 