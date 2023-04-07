import datetime
import json
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List

from bson import ObjectId
from fastapi import APIRouter, UploadFile
from minio.error import S3Error
from pdf2image import convert_from_bytes
from PyPDF2 import PdfReader

from db.miniodb import miniodb
from db.mongodb import mongodb

router = APIRouter(
    prefix="/pdf",
    tags=["pdf"],
)

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

@router.get("/all")
async def get_all_files():
    
    cursor = mongodb["pdf"].find()
    docs = await cursor.to_list(None)
    
    return json.loads(JSONEncoder().encode(docs))


@router.get("/download/{id}")
async def download_pdf(id: str):

    if (pdf_details := await mongodb["pdf"].find_one({"_id": ObjectId(id)})) is None:
        return {}

    miniodb.download_file("../resources/output/"+pdf_details.get("name"), id+".pdf")

    return {}

@router.get("/download/{id}/{page}")
async def download_pdf_page(id: str, page:int):

    if (pdf_details := await mongodb["pdf"].find_one({"_id": ObjectId(id)})) is None:
        return {}

    try:
        response = miniodb.get_file_tmp(id+".pdf")
        images = convert_from_bytes(response.read())
        name = pdf_details.get("name").split(".")[0]
        images[page-1].save(f"../resources/output/{name}_{page}.jpg", "JPEG")
    # Read data from response.
    finally:
        response.close()
        response.release_conn()


    
    return {}


#TODO background task
@router.post("/upload")
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
            miniodb.upload_file(tmp_path, file_id+".pdf")
        except S3Error as exc:
            print("error occurred.", exc)
        

    finally:
        tmp_path.unlink()  # Delete the temp file
        
    return {"filename": file}

#TODO
@router.post("/upload/multiple")
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

@router.delete("/delete/{id}")
async def delete_pdf(id: str):
    
    await mongodb["pdf"].delete_one({
        "_id": ObjectId(id)
    })

    try:
        miniodb.delete_file(id+".pdf")
    except S3Error as exc:
        print("error occurred.", exc)

    return {}