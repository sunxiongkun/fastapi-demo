import logging

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from src.ai_picture import ai_picture_api

logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_headers=["*"],
    allow_origins=["*"],
    allow_methods=["*"],
)


@app.get(path='/health')
async def health():
    return {
      "code": 200,
      "message": 'success',
      "success": True,
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse({
      "code": 500,
      "message": f"{exc=}",
      "success": False,
      "data": [],
    }, status_code=500)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse({
      "code": 422,
      "message": f"{exc=}",
      "success": False,
      "data": [],
    }, status_code=400)


# 添加子路由
app.include_router(ai_picture_api)


def server():
    import uvicorn
    uvicorn.run(
        app="http_server:app",
        host="0.0.0.0",
        port=8080,
    )
    logger.info("http_server start")


if __name__ == '__main__':
    server()
