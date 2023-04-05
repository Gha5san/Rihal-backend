from fastapi import FastAPI, File, UploadFile, Body, status
from starlette.middleware.cors import CORSMiddleware

from PyPDF2 import PdfReader
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from typing import List

import datetime
from typing import List

from db import mongodb, upload_file_minio, delete_file_minio
from minio.error import S3Error

from bson import ObjectId
import json

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


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
        

        data = dict()
        data["name"] = file.filename
        data["upload_time"] = str(datetime.datetime.utcnow())
        data["size"] = file.size
        data["pages"] = number_of_pages

        pdf_data = await mongodb["pdf"].insert_one(data)

        file_id = str(pdf_data.inserted_id)
        try:
            upload_file_minio(tmp_path, file_id+".pdf")
        except S3Error as exc:
            print("error occurred.", exc)
        

    finally:
        tmp_path.unlink()  # Delete the temp file
        
    return {"filename": file}

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

@app.get("/pdf/all")
async def get_all_files():
    
    cursor = mongodb["pdf"].find()
    docs = await cursor.to_list(None)
    
    return json.loads(JSONEncoder().encode(docs))

@app.delete("/pdf/delete/{id}")
async def delete_pdf(id: str):
    
    await mongodb["pdf"].delete_one({
        "_id": ObjectId(id)
    })

    try:
        delete_file_minio(id+".pdf")
    except S3Error as exc:
        print("error occurred.", exc)

    return {}