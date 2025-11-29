#Builder Stage
FROM python:3.12-slim-bullseye As builder

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y libpq-dev gcc

#create the virtual env
RUN python -m venv /opt/venv
#activate teh virtual env
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

#operational stage
FROM python:3.12-slim-bullseye 

RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install -y libpq-dev 
RUN rm -rf /var/lib/apt/lists/*

#get the virtual env from builder stage
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"
ENV CLOUD_APPS CLOUD_RUN

WORKDIR /pythonproject
COPY . ./
CMD ["gunicorn", "--worker-class", "eventlet", "--bind", "0.0.0.0:$PORT", "--workers", "1", "-t", "4", "app:app"]

