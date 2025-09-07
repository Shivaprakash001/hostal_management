import os
from fastapi import FastAPI, Request
from starlette.responses import FileResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from database.db import init_db
from utils.seed_rooms import init_rooms
from utils.seed_admin import seed_admin
from routes.student_routes import router as student_router
from routes.payment_routes_updated import router as payment_router
from routes.room_routes import router as room_router
from routes.auth_routes import router as auth_router
from routes.agentwardan import router as agent_router
from routes.bootstrap_routes import router as bootstrap_router
from routes.upi_routes import router as upi_router
from routes.menu_routes import router as menu_router
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_rooms()
    seed_admin()
    yield

# Configure CORS origins
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")
if cors_origins:
    origins = [origin.strip() for origin in cors_origins.split(",")]
else:
    origins = ["http://localhost:8000", "http://127.0.0.1:8000"]

app = FastAPI(title="Hostel Management System API", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
app.include_router(upi_router)
app.include_router(menu_router)

# Serve static files

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/student")
async def student_dashboard(request: Request):
    return templates.TemplateResponse("student.html", {"request": request})

@app.get("/payment")
async def payment_page(request: Request):
    return templates.TemplateResponse("payment.html", {"request": request})

@app.get("/admin/upi")
async def admin_upi_settings(request: Request):
    return templates.TemplateResponse("admin_upi.html", {"request": request})

@app.get("/admin/payments")
async def admin_payments(request: Request):
    return templates.TemplateResponse("admin_payments.html", {"request": request})

if __name__ == "__main__":
    import uvicorn

    # Get host and port from environment variables (for production deployment)
    host = os.getenv("HOST", "localhost")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(app, host=host, port=port)
