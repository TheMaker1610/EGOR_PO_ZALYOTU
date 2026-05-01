"""Точка входа для FastAPI-сервера."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("ё:app", host="127.0.0.1", port=8000, reload=False)
