FROM python:3.10.13-bookworm

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# RUN mkdir /chatpp

WORKDIR /.

RUN pip install --upgrade pip

COPY . .

RUN pip install -r requirements.txt
 

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]