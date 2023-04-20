FROM python:3.8-slim

WORKDIR /code

# This prevents Python from writing out pyc files
ENV PYTHONDONTWRITEBYTECODE 1

# This keeps Python from buffering stdin/stdout
#ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

RUN python -c "import nltk; nltk.download('stopwords'); nltk.download('punkt')"

# This is required for turning pdf to image 
RUN apt-get update && apt-get -y install poppler-utils

COPY ./app /code/app

COPY ./tests /code/tests

CMD ["uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8080"]
