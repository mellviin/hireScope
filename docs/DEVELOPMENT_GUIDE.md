# Development Guide

## Project Structure Overview

```
hirescope/
├── backend/                          # Python FastAPI backend
│   ├── app/
│   │   ├── main.py                  # FastAPI application entry point
│   │   ├── database/                # Database configuration
│   │   │   └── session.py           # SQLAlchemy session management
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── resume.py
│   │   │   ├── job_description.py
│   │   │   └── match_result.py
│   │   ├── schemas/                 # Pydantic request/response schemas
│   │   │   ├── auth.py
│   │   │   ├── resume.py
│   │   │   ├── job_description.py
│   │   │   └── analysis.py
│   │   ├── routers/                 # API route handlers
│   │   │   ├── auth.py
│   │   │   ├── resume.py
│   │   │   ├── job_description.py
│   │   │   └── analysis.py
│   │   ├── services/                # Business logic
│   │   │   ├── resume_parser.py     # Parse resumes with spaCy
│   │   │   ├── text_extractor.py    # Extract text from PDF/DOCX
│   │   │   ├── jd_analyzer.py       # Analyze job descriptions
│   │   │   ├── match_engine.py      # ATS matching algorithm
│   │   │   ├── resume_optimizer.py  # Generate suggestions
│   │   │   └── docx_exporter.py     # Export to DOCX
│   │   ├── ml/                      # Machine learning
│   │   │   ├── predictor.py         # XGBoost/Random Forest predictor
│   │   │   └── models/              # Pre-trained models
│   │   ├── utils/                   # Utility modules
│   │   │   ├── auth.py              # JWT and password hashing
│   │   │   ├── logging.py           # JSON logging
│   │   │   └── exceptions.py        # Custom exceptions
│   │   ├── data/                    # Data files
│   │   │   └── skill_templates.json # Skill suggestion templates
│   │   └── __init__.py
│   ├── tests/                       # Backend tests
│   │   └── test_api.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/                         # React TypeScript frontend
│   ├── src/
│   │   ├── index.tsx                # Entry point
│   │   ├── App.tsx                  # Main app component
│   │   ├── pages/                   # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── ResumeUpload.tsx
│   │   │   ├── JDAnalysis.tsx
│   │   │   └── matchResults.tsx
│   │   ├── components/              # Reusable components
│   │   │   ├── ATSScoreCard.tsx
│   │   │   └── SkillBadge.tsx
│   │   ├── redux/                   # Redux state management
│   │   │   ├── store.ts
│   │   │   └── slices/
│   │   │       ├── authSlice.ts
│   │   │       ├── resumeSlice.ts
│   │   │       ├── jobDescriptionSlice.ts
│   │   │       └── analysisSlice.ts
│   │   ├── services/                # API services
│   │   │   └── api.ts
│   │   ├── hooks/                   # Custom React hooks
│   │   ├── utils/                   # Utilities
│   │   ├── index.css
│   │   └── App.tsx
│   ├── public/
│   │   ├── index.html
│   │   └── favicon.ico
│   ├── package.json
│   ├── tailwind.config.js
│   └── .env
│
├── docker/                          # Docker configuration
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── docker-compose.yml
│   └── .dockerignore
│
├── docs/                            # Documentation
│   ├── DEPLOYMENT_GUIDE.md
│   ├── DEVELOPMENT_GUIDE.md
│   └── API_REFERENCE.md
│
├── .env.example                     # Example environment variables
└── README.md                        # Project README
```

## Development Workflow

### 1. Code Style and Standards

**Python (Backend)**
```bash
# Format code
black app/

# Check linting
flake8 app/

# Sort imports
isort app/

# Type checking
mypy app/
```

**TypeScript (Frontend)**
```bash
# Format code
npx prettier --write src/

# Lint code
npx eslint src/

# Type checking
npx tsc --noEmit
```

### 2. Running in Development

**Backend with hot reload:**
```bash
cd backend
uvicorn app.main:app --reload
```

**Frontend with hot reload:**
```bash
cd frontend
npm start
```

### 3. Adding New Features

#### Adding a New API Endpoint

1. **Define Schema** (`app/schemas/new_feature.py`):
```python
from pydantic import BaseModel

class NewFeatureRequest(BaseModel):
    field1: str
    field2: int
```

2. **Add Database Model** (`app/models/new_model.py`):
```python
from sqlalchemy import Column, Integer, String
from app.database.session import Base

class NewModel(Base):
    __tablename__ = "new_models"
    id = Column(Integer, primary_key=True)
    field1 = Column(String)
```

3. **Create Service** (`app/services/new_service.py`):
```python
class NewService:
    def process_data(self, data):
        # Business logic
        pass
```

4. **Create Router** (`app/routers/new_feature.py`):
```python
from fastapi import APIRouter, Depends
from app.schemas.new_feature import NewFeatureRequest
from app.services.new_service import NewService

router = APIRouter(prefix="/api/new", tags=["New Feature"])

@router.post("/endpoint")
async def new_endpoint(request: NewFeatureRequest):
    service = NewService()
    result = service.process_data(request)
    return result
```

5. **Register Router** in `main.py`:
```python
from app.routers import new_feature
app.include_router(new_feature.router)
```

### 4. Testing

**Backend unit tests:**
```python
# tests/test_services.py
def test_resume_parser():
    from app.services.resume_parser import ResumeParser
    parser = ResumeParser()
    result = parser.parse_text("sample text")
    assert result['name'] is not None
```

**Run tests:**
```bash
pytest -v
pytest --cov=app tests/
```

### 5. Database Migrations

Using Alembic (optional):
```bash
# Create migration
alembic revision --autogenerate -m "Add new field"

# Apply migration
alembic upgrade head

# Revert migration
alembic downgrade -1
```

## Common Development Tasks

### Task 1: Add a New Skill Category

1. Update `skill_templates.json` in `app/data/`
2. Update skill extraction in `resume_parser.py`
3. Add tests in `tests/test_services.py`

### Task 2: Improve ATS Matching

1. Modify weights in `match_engine.py`
2. Update feature extraction in `ml/predictor.py`
3. Add test cases with known good/bad matches

### Task 3: Add Frontend Page

1. Create page component in `src/pages/`
2. Add Redux slice if needed in `src/redux/slices/`
3. Create API calls in `src/services/api.ts`
4. Add route in `src/App.tsx`

### Task 4: Add Analytics/Logging

1. Implement logging in service methods
2. Add monitoring dashboard (future enhancement)
3. Export logs to cloud (AWS CloudWatch, etc.)

## Performance Tips

### Backend
- Cache NLP models in memory
- Use database indexes for frequently queried fields
- Implement pagination for list endpoints
- Use async/await for I/O operations

### Frontend
- Use React.memo() for expensive components
- Lazy load routes with React.lazy()
- Memoize API calls with useMemo/useCallback
- Optimize bundle size with tree-shaking

## Debugging

### Backend Debug Mode
```python
# In .env
DEBUG=true

# Run with debugging
python -m pdb -m uvicorn app.main:app
```

### Frontend Debug Mode
```javascript
// In browser console
console.log(store.getState()); // View Redux state
```

### Database Inspection
```bash
# SQLite CLI
sqlite3 hirescope.db
.tables
.schema users
SELECT * FROM users;
```

## Release Process

1. Create release branch: `git checkout -b release/v1.0.0`
2. Update version numbers
3. Update CHANGELOG.md
4. Run full test suite
5. Build Docker images
6. Create release tag
7. Deploy to production

## Monitoring and Observability

### Logging
- All services log to stdout (JSON format)
- Use structured logging with context
- Log levels: DEBUG, INFO, WARNING, ERROR

### Metrics (Future)
- User authentication rate
- API response times
- Resume parsing success rate
- ATS score distribution

### Error Tracking (Future)
- Integrate Sentry for error tracking
- Alert on critical errors
- Monitor error rates by endpoint

## Security Checklist

- [ ] All passwords hashed with bcrypt
- [ ] SQL injection prevented (ORM usage)
- [ ] CORS configured correctly
- [ ] JWT tokens validated on all protected routes
- [ ] Input validation on all endpoints
- [ ] Environment variables not in git
- [ ] Secrets stored securely
- [ ] HTTPS enabled in production

## Performance Benchmarks

Target metrics:
- Resume parsing: < 2 seconds
- JD analysis: < 1 second
- ATS matching: < 500ms
- API latency (p95): < 200ms
- Frontend load time: < 3 seconds

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [spaCy NLP](https://spacy.io/)
- [Redux Toolkit](https://redux-toolkit.js.org/)
- [Tailwind CSS](https://tailwindcss.com/)
