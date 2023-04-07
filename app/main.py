from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from api.pdf import router as pdf_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

app.include_router(pdf_router)

@app.get("/")
def root():
    #Simple API
    return {"Hello": "World"}
