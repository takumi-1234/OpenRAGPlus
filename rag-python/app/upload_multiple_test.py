
import os
import shutil
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# Create a directory for uploads if it doesn't exist
UPLOAD_DIR = "uploads_test"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@app.post("/upload_test/")
async def create_upload_files(files: List[UploadFile] = File(...)):
    """
    Uploads multiple files and saves them to the UPLOAD_DIR.
    """
    filenames = []
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="File name not found.")
        
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        filenames.append(file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    return JSONResponse(content={"filenames": filenames})

@app.get("/")
def read_root():
    return {"message": "Welcome to the multiple file upload test API"}
