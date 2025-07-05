# Celery Troubleshooting Guide

## Summary of All Issues Found & Fixed

### Critical Issues Resolved:
1. **Missing App Directory in Docker** - Fixed
2. **Incorrect Import Statements** - Fixed  
3. **Network Configuration Issues** - Fixed
4. **Task Routing Mismatches** - Fixed
5. **Queue Configuration Issues** - Fixed
6. **Variable Name Errors** - Fixed

## Issues Found & Fixed

### 1. **Missing App Directory in Docker**
**Problem**: The Dockerfile wasn't copying the `app/` directory which contains the Celery instance.
**Fix**: Added `COPY app/ ./app/` to Dockerfile.

### 2. **Variable Name Error in Task Code**
**Problem**: Line 158 in `tasks/component_tasks.py` referenced undefined variable `components`.
**Fix**: Changed to `completed_components`.

### 3. **Network Configuration Issues**
**Problem**: Using `network_mode: "host"` was causing networking issues between containers.
**Fix**: Removed `network_mode: "host"` and used proper Docker networking:
- Backend accessible at `localhost:1212` from host
- Services communicate via container names (`redis`, `vaakshakti-db`)
- Ollama accessible via `host.docker.internal:11434`

### 4. **Task Routing Mismatch**
**Problem**: Task names in routing didn't match actual task names.
**Fix**: Updated `celery_app.py` routing to match actual task names.

### 5. **Redis URL Configuration**
**Problem**: Redis URL defaulted to wrong host in different environments.
**Fix**: Updated to use `redis://redis:6379/0` for container networking.

### 6. **Incorrect Import Statements in Task Files**
**Problem**: Tasks in `tasks/speech_evaluation.py` and `tasks/notification.py` were importing from `celery_app` instead of `app.core.celery_instance`.
**Fix**: Updated all import statements to use `from app.core.celery_instance import celery_app`.

### 7. **Missing Default Queue in Worker**
**Problem**: Worker wasn't listening to the default `celery` queue, causing unrouted tasks to fail.
**Fix**: Added `celery` queue to worker command in `entrypoint.sh`.

## How to Test the Setup

### Quick Test (Recommended)
```bash
# Run the comprehensive test script
./run_tests.sh
```

### Individual Tests

#### 1. Test Redis Connection
```bash
docker-compose exec celery-worker python test_celery.py
```

#### 2. Test Task Dispatch
```bash
docker-compose exec speech-tutor python test_task_dispatch.py
```

#### 3. Comprehensive Setup Test
```bash
docker-compose exec speech-tutor python test_full_setup.py
```

#### 4. Monitor Celery Worker Logs
```bash
docker-compose logs -f celery-worker
```

#### 5. Check Redis
```bash
docker-compose exec redis redis-cli
> ping
> keys *
```

#### 6. Check Worker Status
```bash
docker-compose exec speech-tutor python -c "
from app.core.celery_instance import celery_app
inspect = celery_app.control.inspect()
print('Active workers:', inspect.active())
print('Registered tasks:', inspect.registered())
"
```

## Current Architecture

```
Frontend (port 1213) → Backend (host network) → Celery Worker (host network)
                                    ↓                    ↓
                              Redis (port 6379) ←-------
                                    ↓
                            PostgreSQL (port 1211)
                                    ↓
                            Ollama (localhost:11434)
```

**Network Configuration:**
- **Backend & Celery Worker**: Host network mode (can access localhost:11434)
- **Redis & PostgreSQL**: Default Docker network with exposed ports
- **Frontend**: Default Docker network with proxy to backend

## Environment Variables

### Backend & Worker (Host Network)
- `REDIS_URL=redis://localhost:6379/0`
- `DATABASE_URL=postgresql+asyncpg://vaakshakti_user:vaakshakti_password@localhost:1211/vaakshakti_db`
- `OLLAMA_HOST=http://localhost:11434`

### Frontend
- API calls proxied to `localhost:1212` via Vite proxy

## Common Issues & Solutions

### Worker Not Starting
- Check if Redis is healthy: `docker-compose ps`
- Verify entrypoint.sh is executable: `chmod +x entrypoint.sh`
- Check worker logs: `docker-compose logs celery-worker`

### Tasks Not Being Received
- Verify task names match routing configuration
- Check Redis connectivity from both backend and worker
- Ensure tasks are imported properly in celery_app.py

### Network Issues
- Verify `host.docker.internal` is accessible for Ollama
- Check if services can reach each other using container names
- Ensure ports are properly exposed

## Debugging Commands

### Inside Worker Container
```bash
# Enter worker container
docker-compose exec celery-worker bash

# Check registered tasks
celery -A celery_app.celery_app inspect registered

# Check active tasks
celery -A celery_app.celery_app inspect active

# Check worker stats
celery -A celery_app.celery_app inspect stats
```

### Inside Backend Container  
```bash
# Enter backend container
docker-compose exec speech-tutor bash

# Test Redis connection
python -c "import redis; r=redis.Redis(host='redis'); print(r.ping())"

# Check task dispatch
python test_task_dispatch.py
```

## Queue Configuration

The worker listens to these queues:
- `transcription` - Audio transcription tasks
- `audio_processing` - Audio feature extraction
- `text_analysis` - Text analysis tasks
- `llm_feedback` - LLM-based feedback tasks
- `notifications` - Notification tasks
- `speech_evaluation` - Speech evaluation tasks
- `language_analysis` - Language analysis tasks

## Performance Tuning

### Worker Concurrency
Current setting: `--concurrency=2`
Adjust based on your CPU cores and workload.

### Queue Priorities
Consider implementing queue priorities if certain tasks are more important:
```python
celery_app.conf.task_routes = {
    'tasks.component_tasks.transcribe_audio_task': {
        'queue': 'transcription',
        'priority': 9
    },
    # ... other routes
}
```

## Next Steps

1. Start the services: `docker-compose up -d`
2. Check all services are healthy: `docker-compose ps`
3. Test the setup using the test scripts
4. Monitor logs for any issues
5. Test end-to-end by uploading audio through the frontend

## Troubleshooting Checklist

- [ ] All containers are running and healthy
- [ ] Redis is accessible from both backend and worker
- [ ] Tasks are properly registered in Celery
- [ ] Worker is listening to correct queues
- [ ] Network connectivity between containers works
- [ ] Ollama is accessible from containers
- [ ] Frontend can reach backend API
- [ ] Database connections are working