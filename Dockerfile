FROM python:3.12.2
WORKDIR /app

COPY solr_data/ /app/solr_data/
COPY faiss_db/ /app/faiss_db/
COPY tad/ /app/tad/
COPY tvsz /app/tvsz/
COPY requirements.txt /app/
COPY *.py /app/

RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
