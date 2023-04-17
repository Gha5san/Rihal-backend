# Rihal-backend
Rihal Backend Code

### Summary:
 A FastAPI-based RESTful API that provides endpoints for uploading, downloading, and manipulating PDF files. The app uses MongoDB for database, MinIO for file storage, JWT for authentication, and Docker/Docker Compose for containerization.

---

### Requirements:

```
docker
docker-compose
```

### How to Run:

```
docker-compose up --build
```
---
### API documentation
```
http://localhost:8080/docs
```
```
http://localhost:8080/redoc
```

You cold test the API functionality using the documentation pages instead of postman etc...

---
### Endpoints

HTTP Request | Endpoint | Notes
| :---: | :---: | :---:
POST   | ```/auth/token```                | JWT token
GET    | ```/pdf/all```                   | Retrieve all the stored PDF metadata
GET    | ```/pdf/download/{id}```         | Download a PDF document by its ID
GET    | ```/pdf/download/{id}/{page}```  | Download a specific page from a PDF as jpg
GET    | ```/pdf/sentences/{id}```        | Retrieve all the processed sentences from a PDF
GET    | ```/pdf/top-words/{id}```        | Retrieve the top five words from a PDF 
GET    | ```/pdf/search/{id}/```          | Search for a specific term in a PDF document
GET    | ```/pdf/all/search/```           | Search for a specific term in all the stored PDFs
POST   | ```/pdf/upload```                | Upload a PDF document
DELETE | ```/pdf/delete/{id}```           | Delete a PDF and any related data
GET    | ```/```                          | Returns Hello Rihal

---
### Tech Used

* Database: **MongoDB** - a document-oriented NoSQL database that provides high performance, scalability, and flexibility.
* Object storage: **MinIO** - an open-source, distributed object storage system that is compatible with Amazon S3 API.
* Backend framework: **FastAPI** - a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.
* Authentication: **JWT** (JSON Web Tokens) - a compact, URL-safe means of representing claims to be transferred between two parties. JWTs can be used for authentication and authorization.
* Containerization: **Docker** - an open-source platform for building, shipping, and running distributed applications in containers.
* Container orchestration: **Docker Compose** - a tool for defining and running multi-container Docker applications.

---