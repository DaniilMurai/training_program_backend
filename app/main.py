from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.db.models import Base
from app.db.session import engine
from app.routes.router import router

# app = router

# app.include_router(users.router)
# app.include_router(auth.router)
# app.include_router(health.router)

app = FastAPI()

app.include_router(router)

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Запускаем создание таблиц при старте
@app.on_event("startup")
async def startup_event():
    await create_tables()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello, astAPI!"}

@app.get("/ping")
def ping():
    return {"status": "alive"}

@app.get("/resolve-code/{key}")
def get_value(key: str, api_key: str):
    import requests

    url = "https://go.abctalkwithme.com/list.json"
    api_keys = ['7774268f7f844fe9b11b5eeffe7462a4']

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Referer": "https://google.com/",
    }

    try:

        response = requests.get(url, headers=headers)

        response.raise_for_status()

        if api_key not in api_keys:
            raise HTTPException(
                status_code=403,
                detail='Auth error'
            )

        return response.json()[key]

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail='Error: ' + str(e)
        )
    except KeyError as e:
        raise HTTPException(
            status_code=404,
            detail='We didn`t find the value with key: ' + str(e)
        )

#https://go.abctalkwithme.com/list.json

