from fastapi import FastAPI
from db.session import engine, Base
from models import user, house, node, document, audio_log
from routers import house as house_router
from routers import node as node_router
from routers import document as document_router
from routers import auth as auth_router

app = FastAPI(title="Eterna Home Backend API")

app.include_router(auth_router.router)
app.include_router(house_router.router)
app.include_router(node_router.router)
app.include_router(document_router.router)

@app.get("/")
async def root():
    return {"message": "Eterna Home Backend is running!"}

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    print("Database tables created/checked.") 