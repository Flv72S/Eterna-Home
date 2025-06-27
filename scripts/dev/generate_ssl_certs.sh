#!/bin/bash

# 🔒 SSL Certificate Generator for Eterna Home Development
# Genera certificati SSL self-signed per sviluppo locale

set -e

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔒 GENERATORE CERTIFICATI SSL - ETERNA HOME${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Directory per i certificati
CERT_DIR="certs"
mkdir -p "$CERT_DIR"

# Configurazioni
COUNTRY="IT"
STATE="Italy"
CITY="Rome"
ORG="Eterna Home"
ORG_UNIT="Development"
COMMON_NAME="localhost"
VALID_DAYS=365

echo -e "${YELLOW}📋 Configurazione certificati:${NC}"
echo "  - Paese: $COUNTRY"
echo "  - Stato: $STATE"
echo "  - Città: $CITY"
echo "  - Organizzazione: $ORG"
echo "  - Unità: $ORG_UNIT"
echo "  - Nome comune: $COMMON_NAME"
echo "  - Validità: $VALID_DAYS giorni"
echo ""

# 1. Genera chiave privata per MinIO
echo -e "${YELLOW}🔑 1. Generazione chiave privata MinIO...${NC}"
openssl genrsa -out "$CERT_DIR/minio-private.key" 2048
echo -e "${GREEN}✅ Chiave privata MinIO generata: $CERT_DIR/minio-private.key${NC}"

# 2. Genera certificato MinIO
echo -e "${YELLOW}📜 2. Generazione certificato MinIO...${NC}"
openssl req -new -x509 -key "$CERT_DIR/minio-private.key" -out "$CERT_DIR/minio-cert.pem" -days $VALID_DAYS -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$ORG_UNIT/CN=$COMMON_NAME"
echo -e "${GREEN}✅ Certificato MinIO generato: $CERT_DIR/minio-cert.pem${NC}"

# 3. Genera chiave privata per PostgreSQL
echo -e "${YELLOW}🔑 3. Generazione chiave privata PostgreSQL...${NC}"
openssl genrsa -out "$CERT_DIR/postgresql-private.key" 2048
echo -e "${GREEN}✅ Chiave privata PostgreSQL generata: $CERT_DIR/postgresql-private.key${NC}"

# 4. Genera certificato PostgreSQL
echo -e "${YELLOW}📜 4. Generazione certificato PostgreSQL...${NC}"
openssl req -new -x509 -key "$CERT_DIR/postgresql-private.key" -out "$CERT_DIR/postgresql-cert.pem" -days $VALID_DAYS -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$ORG_UNIT/CN=$COMMON_NAME"
echo -e "${GREEN}✅ Certificato PostgreSQL generato: $CERT_DIR/postgresql-cert.pem${NC}"

# 5. Genera chiave privata per Redis
echo -e "${YELLOW}🔑 5. Generazione chiave privata Redis...${NC}"
openssl genrsa -out "$CERT_DIR/redis-private.key" 2048
echo -e "${GREEN}✅ Chiave privata Redis generata: $CERT_DIR/redis-private.key${NC}"

# 6. Genera certificato Redis
echo -e "${YELLOW}📜 6. Generazione certificato Redis...${NC}"
openssl req -new -x509 -key "$CERT_DIR/redis-private.key" -out "$CERT_DIR/redis-cert.pem" -days $VALID_DAYS -subj "/C=$COUNTRY/ST=$STATE/L=$CITY/O=$ORG/OU=$ORG_UNIT/CN=$COMMON_NAME"
echo -e "${GREEN}✅ Certificato Redis generato: $CERT_DIR/redis-cert.pem${NC}"

# 7. Imposta permessi corretti
echo -e "${YELLOW}🔐 7. Impostazione permessi...${NC}"
chmod 600 "$CERT_DIR"/*.key
chmod 644 "$CERT_DIR"/*.pem
echo -e "${GREEN}✅ Permessi impostati correttamente${NC}"

# 8. Crea file di configurazione per i servizi
echo -e "${YELLOW}📝 8. Creazione file di configurazione...${NC}"

# MinIO configuration
cat > "$CERT_DIR/minio-config.env" << EOF
# MinIO SSL Configuration
MINIO_CERT_FILE=./certs/minio-cert.pem
MINIO_KEY_FILE=./certs/minio-private.key
MINIO_USE_SSL=true
MINIO_VERIFY_SSL=true
EOF

# PostgreSQL configuration
cat > "$CERT_DIR/postgresql-ssl.conf" << EOF
# PostgreSQL SSL Configuration
ssl = on
ssl_cert_file = './certs/postgresql-cert.pem'
ssl_key_file = './certs/postgresql-private.key'
ssl_ca_file = './certs/postgresql-cert.pem'
EOF

# Redis configuration
cat > "$CERT_DIR/redis-ssl.conf" << EOF
# Redis SSL Configuration
tls-port 6380
tls-cert-file ./certs/redis-cert.pem
tls-key-file ./certs/redis-private.key
tls-ca-cert-file ./certs/redis-cert.pem
EOF

echo -e "${GREEN}✅ File di configurazione creati${NC}"

# 9. Riepilogo finale
echo ""
echo -e "${BLUE}📊 RIEPILOGO CERTIFICATI GENERATI${NC}"
echo -e "${BLUE}================================${NC}"
echo ""
echo -e "${GREEN}✅ MinIO:${NC}"
echo "  - Chiave: $CERT_DIR/minio-private.key"
echo "  - Certificato: $CERT_DIR/minio-cert.pem"
echo "  - Config: $CERT_DIR/minio-config.env"
echo ""
echo -e "${GREEN}✅ PostgreSQL:${NC}"
echo "  - Chiave: $CERT_DIR/postgresql-private.key"
echo "  - Certificato: $CERT_DIR/postgresql-cert.pem"
echo "  - Config: $CERT_DIR/postgresql-ssl.conf"
echo ""
echo -e "${GREEN}✅ Redis:${NC}"
echo "  - Chiave: $CERT_DIR/redis-private.key"
echo "  - Certificato: $CERT_DIR/redis-cert.pem"
echo "  - Config: $CERT_DIR/redis-ssl.conf"
echo ""

# 10. Istruzioni per l'uso
echo -e "${YELLOW}📋 ISTRUZIONI PER L'USO:${NC}"
echo ""
echo "1. **MinIO SSL:**"
echo "   - Copia i file in $CERT_DIR/minio-cert.pem e $CERT_DIR/minio-private.key"
echo "   - Avvia MinIO con: minio server --certs-dir ./certs"
echo ""
echo "2. **PostgreSQL SSL:**"
echo "   - Aggiungi al postgresql.conf:"
echo "     ssl = on"
echo "     ssl_cert_file = './certs/postgresql-cert.pem'"
echo "     ssl_key_file = './certs/postgresql-private.key'"
echo ""
echo "3. **Redis SSL:**"
echo "   - Avvia Redis con: redis-server --tls-port 6380 --tls-cert-file ./certs/redis-cert.pem --tls-key-file ./certs/redis-private.key"
echo ""
echo "4. **Environment Variables:**"
echo "   - Aggiorna il file .env con:"
echo "     MINIO_USE_SSL=true"
echo "     DATABASE_SSL_MODE=require"
echo "     REDIS_SSL=true"
echo ""

echo -e "${GREEN}🎉 Certificati SSL generati con successo!${NC}"
echo -e "${YELLOW}⚠️  RICORDA: Questi sono certificati self-signed per sviluppo.${NC}"
echo -e "${YELLOW}   In produzione usa certificati firmati da una CA autorizzata.${NC}" 