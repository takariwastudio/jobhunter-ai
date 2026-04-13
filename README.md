# JobHunter AI

Automatización de búsqueda de empleo impulsada por IA. Sube tu CV y deja que la inteligencia artificial busque y sugiera empleos que coincidan con tu perfil.

## Características

- 📄 **Subida de CV**: Soporte para PDF, Word, TXT e imágenes
- 🤖 **Análisis con IA**: Extracción automática de información usando Claude
- 📝 **Edición de perfil**: Revisa y corrige la información extraída
- 🔍 **Búsqueda de empleos**: (Próximamente) Encuentra vacantes relevantes
- 📊 **Matching inteligente**: (Próximamente) IA compara tu perfil con empleos
- ✉️ **Cover letters**: (Próximamente) Genera cartas de presentación personalizadas

## Arquitectura

- **Backend**: Python + FastAPI + PostgreSQL + Redis
- **Frontend**: React + TypeScript + Tailwind CSS + Vite
- **IA**: Anthropic Claude 3.5 Sonnet

## Requisitos

- Docker + Docker Compose
- Node.js 20+ (para desarrollo local frontend)
- Python 3.11+ (para desarrollo local backend)
- API Key de Anthropic

## Inicio Rápido

1. **Clonar y configurar**:
```bash
cd jobhunter-ai
# Crear archivo de variables de entorno
cp .env.example .env
# Editar .env y agregar tu ANTHROPIC_API_KEY
```

2. **Iniciar con Docker**:
```bash
docker-compose up --build
```

3. **Acceder a la aplicación**:
- Frontend: http://localhost:5173
- API Docs: http://localhost:8000/docs

## Desarrollo Local

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurar variables de entorno
export DATABASE_URL="postgresql://jobhunter:jobhunter123@localhost:5432/jobhunter"
export ANTHROPIC_API_KEY="tu-api-key"

# Iniciar
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Estructura del Proyecto

```
jobhunter-ai/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── models/          # SQLAlchemy models
│   │   ├── routers/         # API endpoints
│   │   ├── services/        # Business logic
│   │   └── schemas/         # Pydantic schemas
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/           # React pages
│   │   ├── components/      # Reusable components
│   │   └── services/        # API client
│   └── package.json
└── docker-compose.yml
```

## Variables de Entorno

```bash
# Backend
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0
ANTHROPIC_API_KEY=sk-ant-api03-...
SECRET_KEY=your-secret-key

# Frontend
VITE_API_URL=http://localhost:8000/api/v1
```

## Roadmap

- [x] MVP: Subida y parsing de CV
- [x] Extracción de información con IA
- [x] Edición de perfil
- [ ] Búsqueda de empleos (APIs externas)
- [ ] Matching perfil-vacante con IA
- [ ] Generación de cover letters
- [ ] Automatización de aplicaciones
- [ ] Dashboard de seguimiento

## Contribuir

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la branch (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## Licencia

MIT License
