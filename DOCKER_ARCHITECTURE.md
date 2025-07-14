# TKA Voice Agent - Docker Compose Overview

This document provides a comprehensive overview of the fully dockerized TKA Voice Agent system.

## 🐳 **Container Architecture**

### **Core Services**
```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │      Redis      │  │    pgAdmin      │
│   Database      │  │     Cache       │  │   DB Admin      │
│   Port: 5432    │  │   Port: 6379    │  │   Port: 5050    │
└─────────────────┘  └─────────────────┘  └─────────────────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                ┌─────────────────────────────┐
                │      Backend Service        │
                │    FastAPI + Services       │
                │       Port: 8000           │
                └─────────────────────────────┘
                               │
                ┌─────────────────────────────┐
                │       ngrok Tunnel          │
                │    Webhook Exposure         │
                │    Web UI: Port 4040        │
                └─────────────────────────────┘
                               │
                ┌─────────────────────────────┐
                │      Test Runner            │
                │    Isolated Testing         │
                │     (On Demand)            │
                └─────────────────────────────┘
```

## 📦 **Service Details**

### **1. PostgreSQL Database (`postgres`)**
- **Image**: `postgres:15-alpine`
- **Container**: `tka_postgres`
- **Port**: `5432:5432`
- **Purpose**: Primary data storage for patients, calls, transcriptions
- **Health Check**: `pg_isready` command
- **Data**: Persistent volume `postgres_data`

### **2. Redis Cache (`redis`)**
- **Image**: `redis:7-alpine`
- **Container**: `tka_redis`
- **Port**: `6379:6379`
- **Purpose**: Session storage, caching, real-time data
- **Health Check**: `redis-cli ping`
- **Data**: Persistent volume `redis_data`

### **3. Backend Service (`backend`)**
- **Build**: `./backend/Dockerfile`
- **Container**: `tka_backend`
- **Port**: `8000:8000`
- **Purpose**: FastAPI app with all services (Twilio, STT, AI, etc.)
- **Dependencies**: PostgreSQL, Redis
- **Health Check**: `/health` endpoint
- **Volumes**: Code mounting for development

### **4. pgAdmin (`pgadmin`)**
- **Image**: `dpage/pgadmin4:latest`
- **Container**: `tka_pgadmin`
- **Port**: `5050:80`
- **Purpose**: Database administration interface
- **Credentials**: `admin@tka.com` / `admin`
- **Data**: Persistent volume `pgadmin_data`

### **5. ngrok Tunnel (`ngrok`)**
- **Build**: `./ngrok/Dockerfile`
- **Container**: `tka_ngrok`
- **Port**: `4040:4040` (web interface)
- **Purpose**: Expose backend to internet for Twilio webhooks
- **Dependencies**: Backend service
- **Config**: `./ngrok/ngrok.yml`

### **6. Test Runner (`test-runner`)**
- **Build**: `./tests/Dockerfile`
- **Container**: `tka_test_runner`
- **Purpose**: Isolated testing environment
- **Dependencies**: All services
- **Usage**: On-demand testing with pytest

## 🔧 **Environment Configuration**

All services use environment variables from `.env` file:

```properties
# Database
DATABASE_URL=postgresql://user:password@postgres:5432/tka_voice
REDIS_URL=redis://redis:6379

# Twilio
TWILIO_ACCOUNT_SID=AC3123f54e85931d681c837b9b16f653a1
TWILIO_AUTH_TOKEN=0e8b66594f0f9b5f57c35023c89a0334
TWILIO_PHONE_NUMBER=+18776589089
TWILIO_WEBHOOK_URL=https://your-ngrok-url.com

# AI Services
GEMINI_API_KEY=your_gemini_api_key_here

# ngrok
NGROK_AUTHTOKEN=2lcpQfgaJSDW9sYoEUAebfPIWkd_2WBqSjh1pGG5qMaDX3zzN
```

## 🚀 **Deployment Commands**

### **Windows**
```batch
# Complete deployment
.\scripts\deploy.bat

# Individual operations
docker-compose up -d                    # Start all services
docker-compose down                     # Stop all services
docker-compose restart                  # Restart services
docker-compose logs -f backend          # View logs
.\scripts\test_components.bat           # Run tests
```

### **Linux/macOS**
```bash
# Complete deployment
./scripts/deploy.sh

# Individual operations
docker-compose up -d                    # Start all services
docker-compose down                     # Stop all services
docker-compose restart                  # Restart services
docker-compose logs -f backend          # View logs
./scripts/test_components.sh            # Run tests
```

## 🧪 **Testing Strategy**

### **1. Component Tests**
- **Health Checks**: All services respond correctly
- **Database**: Connection, migrations, basic operations
- **Redis**: Connection, read/write operations
- **API**: All endpoints return expected responses
- **Webhooks**: Twilio webhook simulation
- **ngrok**: Tunnel connectivity

### **2. Integration Tests**
- **Call Flow**: End-to-end call simulation
- **Speech Processing**: Audio → Text → AI Response
- **Notifications**: Alert generation and routing
- **Data Persistence**: Database operations

### **3. Unit Tests**
- **Service Isolation**: Each service tested independently
- **Mock Dependencies**: External APIs mocked
- **Error Handling**: Exception scenarios
- **Data Validation**: Input/output validation

## 📊 **Monitoring & Debugging**

### **Service Health**
```bash
# Check all container status
docker-compose ps

# Health check specific service
curl http://localhost:8000/health

# Check database
docker exec tka_postgres pg_isready -U user -d tka_voice

# Check Redis
docker exec tka_redis redis-cli ping

# Get ngrok URL
curl http://localhost:4040/api/tunnels | jq '.tunnels[0].public_url'
```

### **Logs**
```bash
# All services
docker-compose logs

# Specific service
docker-compose logs -f backend
docker-compose logs -f ngrok
docker-compose logs -f postgres

# Tail logs
docker-compose logs --tail=100 -f
```

### **Debugging**
```bash
# Enter container shell
docker exec -it tka_backend bash
docker exec -it tka_postgres psql -U user -d tka_voice

# Check network connectivity
docker network ls
docker network inspect surgical-care-companion_tka_network
```

## 🔒 **Security Considerations**

### **Production Hardening**
1. **Environment Variables**: Never commit real credentials
2. **Network Isolation**: Use custom Docker networks
3. **Volume Permissions**: Secure file system access
4. **SSL/TLS**: Use HTTPS for all external communication
5. **Secrets Management**: Use Docker secrets for sensitive data

### **Development Safety**
1. **Local Only**: Services bound to localhost
2. **Test Data**: Use mock/test data only
3. **Isolation**: Containers isolated from host system
4. **Clean Shutdown**: Proper service termination

## 📈 **Scaling Considerations**

### **Horizontal Scaling**
- **Backend**: Multiple backend containers with load balancer
- **Database**: Read replicas, connection pooling
- **Redis**: Redis Cluster for high availability
- **ngrok**: Multiple tunnels for load distribution

### **Vertical Scaling**
- **Resources**: Adjust container CPU/memory limits
- **Connections**: Tune database connection pools
- **Cache**: Optimize Redis memory usage
- **Storage**: Use faster storage for database

## 🎯 **Production Deployment**

For production deployment:

1. **Replace ngrok** with proper reverse proxy (nginx, ALB)
2. **Use managed databases** (RDS, ElastiCache)
3. **Container orchestration** (Kubernetes, ECS)
4. **Monitoring** (Prometheus, Grafana)
5. **Logging** (ELK stack, CloudWatch)
6. **CI/CD** (GitHub Actions, GitLab CI)

This Docker setup provides a complete, scalable foundation for the TKA Voice Agent system with all dependencies included and isolated component testing capabilities.
