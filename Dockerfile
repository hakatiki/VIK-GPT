FROM python:3.10
WORKDIR /app
COPY . /app
RUN pip install notebook
RUN pip install -r requirements.txt
EXPOSE 8888
ENV JUPYTER_TOKEN=fc652003cbd10405ed2d401eb375f2f6cf42e7dab43a39a7
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--NotebookApp.token=fc652003cbd10405ed2d401eb375f2f6cf42e7dab43a39a7", "--allow-root"]
