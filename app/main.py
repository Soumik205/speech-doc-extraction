from fastapi import FastAPI

from app.api.v1.transcribe import router as transcribe_router


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(transcribe_router)
    return app


app = create_app()
