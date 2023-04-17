import datetime
import io
import json
import os
import shutil
from pathlib import Path as FilePath
from string import punctuation
from tempfile import NamedTemporaryFile
from typing import List

import nltk
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, status
from fastapi.responses import StreamingResponse
from minio.error import S3Error
from pdf2image import convert_from_bytes
from PIL import Image
from pydantic import BaseModel
from PyPDF2 import PdfReader

from app.api.auth import get_current_active_user
from app.db.miniodb import miniodb
from app.db.mongodb import mongodb

router = APIRouter(
    prefix="/pdf",
    tags=["pdf"], # Tags for documentation purposes
    dependencies=[Depends(get_current_active_user)]
)

# A custom JSONEncoder to handle ObjectId objects in mongodb
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

def save_upload_file_tmp(upload_file: UploadFile) -> FilePath:
    """
    Saves an uploaded file to a temporary file and returns the path to it.

    Parameters:
    -----------
    upload_file : UploadFile
        An instance of `UploadFile` that represents the uploaded file.

    Returns:
    --------
    tmp_path : FilePath
        A `str` or `pathlib.Path` object that represents the path to the saved temporary file.
    """
    try:
        suffix = FilePath(upload_file.filename).suffix
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(upload_file.file, tmp)
            tmp_path = FilePath(tmp.name)
    finally:
        upload_file.file.close()
    return tmp_path

async def get_pdf_details(id: str):
    """
    Gets the details of a PDF file with the given id from the specified MongoDB collection.

    Parameters:
    -----------
    id : str
        A `str` that represents the ObjectId of the PDF file in the MongoDB collection.

    Returns:
    --------
    pdf_details : dict (json)
        A `dict` object that contains the details of the PDF file if it exists in the collection, otherwise raises a `HTTPException`.
    """
    if (pdf_details := await mongodb["pdf"].find_one({"_id": ObjectId(id)})) is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail = f"No pdf file exists with the given id {id}"
            )
    return pdf_details

@router.get("/all")
async def get_all_files():

    # Excluding the "sentences_id" field from the query
    cursor = mongodb["pdf"].find({}, {"sentences_id": 0})
    
    docs = await cursor.to_list(None)
    
    return json.loads(JSONEncoder().encode(docs))


@router.get("/download/{id}")
async def download_pdf(id: str):
    """
    Downloads the PDF file with the given ID from MinIO and streams the file as a response with the appropriate headers.

    Parameters:
    -----------
        id (str): The ID of the PDF file to be downloaded.

    Returns:
    --------
        StreamingResponse: A StreamingResponse object containing the file data and headers for downloading the file.
    """

    pdf_details = await get_pdf_details(id)
    file_data = miniodb.get_file_tmp(id+".pdf").read()
    file_name = pdf_details.get("name")

    return StreamingResponse(io.BytesIO(file_data), media_type='application/pdf', headers={
        'Content-Disposition': f'attachment; filename="{file_name}"'
    })

@router.get("/download/{id}/{page}")
async def download_pdf_page(id: str, page:int):
    """
    Downloads a single page of a PDF file and returns it as a JPEG image.

    Parameters:
    -----------
        id (str): The ID of the PDF file to download.
        page (int): The page number of the PDF file to download.

    Returns:
    --------
        StreamingResponse: The JPEG image of the specified PDF file page.
    """
    pdf_details = await get_pdf_details(id)

    # Check if the specified page number is valid.
    if page > pdf_details.get("pages") or page < 1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = f"Invalid page number"
        )
    with NamedTemporaryFile(suffix=".pdf") as tmp_file:
        miniodb.download_file(tmp_file.name, id + ".pdf")
        pdf_bytes = tmp_file.read()

        images = convert_from_bytes(pdf_bytes)
        if page > len(images):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Invalid page number"
            )

        image_bytes = io.BytesIO()
        images[page - 1].save(image_bytes, "JPEG")
        image_bytes.seek(0)

        return StreamingResponse(image_bytes, media_type="image/jpeg", headers={
            "Content-Disposition": f'attachment; filename="{pdf_details.get("name").split(".")[0]}_p{page}.jpg"'
        })


@router.get("/sentences/{id}")
async def get_pdf_sentences(id: str):
    """
    A route to get the sentences extracted from a PDF file with the given id.

    Parameters:
    -----------
    id (str): A string representing the id of the PDF file.

    Returns:
    --------
    json: A json representing the extracted sentences.
    """
    pdf_details = await get_pdf_details(id)

    sentences = await mongodb["sentences"].find_one({"_id": pdf_details["sentences_id"]}, 
                                        {"_id": 0})
    
    return sentences

@router.get("/top-words/{id}")
async def get_top_words(id: str):
    """
    Retrieves the extracted sentences from a PDF file with the given id.

    Parameters:
    -----------
    id (str): The id of the PDF file.

    Returns:
    --------
    json: A json representing the extracted sentences.
    """

    #plural and singular words are considered different

    sentences = await get_pdf_sentences(id)

    #Cast it to lowercase string and remove any punctuations
    sentences = " ".join(sentences["sentences"]).translate(
        str.maketrans("", "", punctuation)).lower()

    #Maybe add it as configuration in docker file?
    nltk.download('stopwords')

    process_words = nltk.tokenize.word_tokenize(sentences)
    english_stopwords = nltk.corpus.stopwords.words('english')
    common_words = nltk.FreqDist(
        w for w in process_words if w not in english_stopwords)

    words = dict()
    words["top-words"] = dict(enumerate(common_words.most_common(5)))
    
    # format {top-words: {0: [word, number of occurrence]}}

    return words

@router.get("/search/{id}/")
async def search_pdf(id: str, search: str):
    """
    A route to search for a specific string in the sentences extracted from a PDF file with the given id.

    Parameters:
    -----------
    id (str): A string representing the id of the PDF file.
    search (str): A string to search for in the extracted sentences.

    Returns:
    --------
    json: A json representing the number of occurrences and the sentences containing the search string.
    """
    sentences = await get_pdf_sentences(id)
    sentences = sentences["sentences"]
    
    total_count = 0
    search_sentences = list()
    for sen in sentences:
        count = sen.lower().count(search)
        if count:
            total_count += count
            search_sentences.append(sen)
        
    return {"occurrence": total_count, "sentences": search_sentences}

@router.get("/all/search/")
async def search_pdf_all(search: str):
    """
    A route to search for a keyword in all PDF files and return a list of PDF ids with the keyword and its count.

    Parameters:
    -----------
    search (str): A string representing the keyword to search for.

    Returns:
    --------
    json: A JSON object representing the search result with PDF ids containing the keyword and its count.
    """

    # Retrieve all PDF documents in the collection
    cursor = mongodb["pdf"].find({}, {"_id": 1})
    docs = await cursor.to_list(None)

    # Convert the BSON documents to JSON
    pdf_list = json.loads(JSONEncoder().encode(docs))

    # Search over each document
    data = dict() 
    data["ids"] = list()
    for pdf in pdf_list:
        id = pdf["_id"]
        search_result = await search_pdf(id, search)

        # If the pdf document contains the word, store the ID and the search result
        if search_result["occurrence"]:
            data["ids"].append(id)
            data[id] = search_result

    return data

#TODO background task
@router.post("/upload")
async def upload_pdf(file: UploadFile):
    """
    A route to upload a PDF file.

    Parameters:
    -----------
    - file (file): The PDF file to upload.

    Returns:
    --------
    - json: A json representing the uploaded PDF file, 
    containing its id, name, upload time, size, number of pages, and id of the sentences extracted from the file.
    """

    # Validate file format to be only pdf
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f'File {file.filename} is not pdf',
        )
    
    # Temporary save the file to process 
    tmp_path = save_upload_file_tmp(file)
    try:
        # Extract text
        reader = PdfReader(tmp_path)
        number_of_pages = len(reader.pages)
        page = reader.pages[0]
        text = page.extract_text()

        # Tokenize the text into sentences
        nltk.download('punkt')
        tokenizer = nltk.data.load('tokenizers/punkt/PY3/english.pickle')
        sentences = dict()
        sentences["sentences"] = tokenizer.tokenize(text)

        # Save the sentences into mongodb
        # Sentences are stored separately from metadata to improve db speed in case it's long
        pdf_sentences = await mongodb["sentences"].insert_one(sentences)

         # Save the metadata of the pdf file into mongodb
        data = dict()
        data["name"] = file.filename
        data["upload_time"] = str(datetime.datetime.utcnow())
        data["size"] = file.size
        data["pages"] = number_of_pages
        data["sentences_id"] = pdf_sentences.inserted_id

        pdf_data = await mongodb["pdf"].insert_one(data)

        # Upload the pdf file to the object storage (minIO)
        file_id = str(pdf_data.inserted_id)
        try:
            miniodb.upload_file(tmp_path, file_id+".pdf")
        except S3Error as exc:
            print("error occurred.", exc)
        

    finally:
        tmp_path.unlink()  # Delete the temp file
        
    return {"id": file_id}


@router.delete("/delete/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pdf(id: str):
    """
    This route deletes a PDF file and its associated sentences from the database and MinIO storage.

    Parameters:
    -----------
    id (str): A string representing the id of the PDF file to be deleted.

    Returns:
    --------
    None.
    """
    
    pdf_details = await get_pdf_details(id)

    await mongodb["sentences"].delete_one({
        "_id": pdf_details["sentences_id"]
    })

    await mongodb["pdf"].delete_one({
        "_id": ObjectId(id)
    })

    try:
        miniodb.delete_file(id+".pdf")
    except S3Error as exc:
        print("error occurred.", exc)

    return 