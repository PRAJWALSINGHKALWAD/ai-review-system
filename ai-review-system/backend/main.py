from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from review_routes import router as review_router
from database import Base, engine

# create DB tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Review System - Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review_router, tags=["reviews"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
