from typing import List, Optional, Dict, Any
from sqlmodel import Session, select, func
from app.models import AudioLog, User, House, Node
from app.schemas.audio_log import AudioLogCreate, AudioLogUpdate, VoiceCommandRequest
from app.models.user import User

class AudioLogService:
    """Servizio per la gestione degli AudioLog."""
    
    @staticmethod
    def create_audio_log(db: Session, audio_log_data: AudioLogCreate, current_user: User) -> AudioLog:
        """Crea un nuovo AudioLog."""
        # Verifica che l'utente esista
        if audio_log_data.user_id != current_user.id:
            raise ValueError("Non puoi creare AudioLog per altri utenti")
        
        # Verifica che la casa appartenga all'utente (se specificata)
        if audio_log_data.house_id:
            house = db.exec(select(House).where(House.id == audio_log_data.house_id)).first()
            if not house or house.owner_id != current_user.id:
                raise ValueError("Casa non trovata o non hai i permessi")
        
        # Verifica che il nodo appartenga alla casa (se specificato)
        if audio_log_data.node_id and audio_log_data.house_id:
            node = db.exec(
                select(Node).where(
                    Node.id == audio_log_data.node_id,
                    Node.house_id == audio_log_data.house_id
                )
            ).first()
            if not node:
                raise ValueError("Nodo non trovato nella casa specificata")
        
        # Crea il nuovo AudioLog
        audio_log = AudioLog(**audio_log_data.dict())
        db.add(audio_log)
        db.commit()
        db.refresh(audio_log)
        return audio_log
    
    @staticmethod
    def get_audio_log(db: Session, log_id: int, current_user: User) -> Optional[AudioLog]:
        """Ottiene un AudioLog specifico."""
        audio_log = db.exec(
            select(AudioLog)
            .where(
                AudioLog.id == log_id,
                AudioLog.user_id == current_user.id
            )
        ).first()
        return audio_log
    
    @staticmethod
    def get_audio_logs(
        db: Session, 
        current_user: User,
        house_id: Optional[int] = None,
        node_id: Optional[int] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Ottiene la lista degli AudioLog con filtri e paginazione."""
        query = (
            select(AudioLog)
            .where(AudioLog.user_id == current_user.id)
        )
        
        # Applica filtri
        if house_id:
            query = query.where(AudioLog.house_id == house_id)
        if node_id:
            query = query.where(AudioLog.node_id == node_id)
        if status:
            query = query.where(AudioLog.processing_status == status)
        
        # Conta totale
        total_query = (
            select(func.count(AudioLog.id))
            .where(AudioLog.user_id == current_user.id)
        )
        if house_id:
            total_query = total_query.where(AudioLog.house_id == house_id)
        if node_id:
            total_query = total_query.where(AudioLog.node_id == node_id)
        if status:
            total_query = total_query.where(AudioLog.processing_status == status)
        
        total = db.exec(total_query).first()
        
        # Applica paginazione e ordinamento
        query = query.order_by(AudioLog.timestamp.desc()).offset(skip).limit(limit)
        audio_logs = db.exec(query).all()
        
        return {
            "items": audio_logs,
            "total": total,
            "page": skip // limit + 1,
            "size": limit,
            "pages": (total + limit - 1) // limit
        }
    
    @staticmethod
    def update_audio_log(
        db: Session, 
        log_id: int, 
        audio_log_data: AudioLogUpdate, 
        current_user: User
    ) -> Optional[AudioLog]:
        """Aggiorna un AudioLog."""
        audio_log = AudioLogService.get_audio_log(db, log_id, current_user)
        if not audio_log:
            return None
        
        # Aggiorna i campi
        update_data = audio_log_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(audio_log, field, value)
        
        db.add(audio_log)
        db.commit()
        db.refresh(audio_log)
        return audio_log
    
    @staticmethod
    def delete_audio_log(db: Session, log_id: int, current_user: User) -> bool:
        """Elimina un AudioLog."""
        audio_log = AudioLogService.get_audio_log(db, log_id, current_user)
        if not audio_log:
            return False
        
        db.delete(audio_log)
        db.commit()
        return True
    
    @staticmethod
    def process_voice_command(
        db: Session, 
        command_data: VoiceCommandRequest, 
        current_user: User
    ) -> AudioLog:
        """Processa un comando vocale e crea un AudioLog."""
        # Crea i dati per AudioLog
        audio_log_data = AudioLogCreate(
            user_id=current_user.id,
            node_id=command_data.node_id,
            house_id=command_data.house_id,
            transcribed_text=command_data.transcribed_text,
            processing_status="received"
        )
        
        # Crea l'AudioLog
        audio_log = AudioLogService.create_audio_log(db, audio_log_data, current_user)
        
        # TODO: In futuro, qui si invierà il messaggio alla coda per elaborazione NLP
        # await send_to_queue(audio_log.id, command_data.transcribed_text)
        
        return audio_log
    
    @staticmethod
    def get_processing_statuses() -> List[str]:
        """Restituisce gli stati di elaborazione disponibili."""
        return ['received', 'transcribing', 'analyzing', 'completed', 'failed']
    
    @staticmethod
    def get_user_voice_stats(db: Session, current_user: User) -> Dict[str, Any]:
        """Ottiene statistiche sui comandi vocali dell'utente."""
        # Conta totale comandi
        total_commands = db.exec(
            select(func.count(AudioLog.id))
            .where(AudioLog.user_id == current_user.id)
        ).first()
        
        # Conta per stato
        status_counts = db.exec(
            select(
                AudioLog.processing_status,
                func.count(AudioLog.id).label("count")
            )
            .where(AudioLog.user_id == current_user.id)
            .group_by(AudioLog.processing_status)
        ).all()
        
        # Conta per casa
        house_counts = db.exec(
            select(
                AudioLog.house_id,
                func.count(AudioLog.id).label("count")
            )
            .where(AudioLog.user_id == current_user.id)
            .group_by(AudioLog.house_id)
        ).all()
        
        return {
            "total_commands": total_commands,
            "status_breakdown": dict(status_counts),
            "house_breakdown": dict(house_counts)
        } 