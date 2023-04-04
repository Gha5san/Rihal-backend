from fastapi import FastAPI, File, UploadFile, Body, status
from starlette.middleware.cors import CORSMiddleware

from PyPDF2 import PdfReader
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from typing import List

import datetime
from typing import List


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

@app.get("/")
def root():
    #Simple API
    return {"Hello": "World"}


#TODO background task
@app.post("/pdf/upload")
async def upload_pdf(file: UploadFile):
    
    #Temporary save the file to process
    tmp_path = save_upload_file_tmp(file)
    try:
        reader = PdfReader(tmp_path)
        number_of_pages = len(reader.pages)
        page = reader.pages[0]
        text = page.extract_text()

    finally:
        tmp_path.unlink()  # Delete the temp file
        
    return {"filename": file,
            "content": text}

#TODO
@app.post("/pdf/upload/multiple")
async def upload_pdf_multiple(files: List[UploadFile]):
    return {"filenames": [file.filename for file in files]}


def save_upload_file_tmp(upload_file: UploadFile) -> Path:
    try:
        suffix = Path(upload_file.filename).suffix
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(upload_file.file, tmp)
            tmp_path = Path(tmp.name)
    finally:
        upload_file.file.close()
    return tmp_path