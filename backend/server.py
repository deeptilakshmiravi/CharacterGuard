from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import routers
# from backend.routes import run_tests, results, comparison

# --------------------------------------------------
# Logging setup
# --------------------------------------------------
# logging.basicConfig(
    # level=logging.INFO,
    # format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
# )
# logger = logging.getLogger(__name__)


app = FastAPI(
    title="CharacterGuard API",
    description="API for testing and evaluating AI character robustness",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change to specific URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(run_tests.router, prefix="/run", tags=["Run Tests"])
app.include_router(results.router, prefix="/results", tags=["Results"])
app.include_router(comparison.router, prefix="/compare", tags=["Comparison"])


@app.get("/")
def root():
    return {
        "message": "CharacterGuard API is running",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.on_event("startup")
def on_startup():
    logger.info("CharacterGuard API started")

@app.on_event("shutdown")
def on_shutdown():
    logger.info("CharacterGuard API stopped")