#!/usr/bin/env python3
"""
Script semplice per testare il sistema di logging.
"""
import sys
import os

# Aggiungi il path dell'app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.core.logging import setup_logging, get_logger, set_trace_id, get_trace_id
    
    print("✅ Import del modulo logging riuscito")
    
    # Configura il logging
    setup_logging(level="DEBUG", json_format=True, include_trace_id=True)
    print("✅ Configurazione logging completata")
    
    # Ottieni un logger
    logger = get_logger("test")
    print("✅ Logger ottenuto")
    
    # Test Trace ID
    trace_id = get_trace_id()
    print(f"✅ Trace ID generato: {trace_id}")
    
    # Test logging
    logger.info("Test del sistema di logging", 
                test_field="test_value",
                numeric_field=123,
                boolean_field=True)
    print("✅ Log inviato con successo")
    
    # Test Trace ID personalizzato
    set_trace_id("custom-trace-123")
    custom_trace_id = get_trace_id()
    print(f"✅ Trace ID personalizzato: {custom_trace_id}")
    
    logger.info("Test con Trace ID personalizzato", 
                custom_trace="test")
    print("✅ Log con Trace ID personalizzato inviato")
    
    print("\n🎉 Tutti i test del logging sono passati!")
    
except Exception as e:
    print(f"❌ Errore: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 