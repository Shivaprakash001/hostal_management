from fastapi import FastAPI, Request
from starlette.responses import FileResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from database.db import init_db
from utils.seed_rooms import init_rooms
from routes.student_routes import router as student_router
from routes.payment_routes import router as payment_router
from routes.room_routes import router as room_router
from routes.auth_routes import router as auth_router
from routes.agentwardan import router as agent_router
from routes.bootstrap_routes import router as bootstrap_router
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_rooms()
    yield

app = FastAPI(title="Hostel Management System API", lifespan=lifespan)
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(student_router)
app.include_router(payment_router)
app.include_router(room_router)
app.include_router(auth_router)
app.include_router(bootstrap_router)
app.include_router(agent_router)

# Serve static files

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    import sys
    
    # Get port from command line arguments or use default 8000
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1] == "--port":
        try:
            port = int(sys.argv[2])
        except (IndexError, ValueError):
            print("Invalid port specified. Using default port 8000.")
    
    uvicorn.run(app, host="localhost", port=port)
