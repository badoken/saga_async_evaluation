FROM python:3

WORKDIR /usr/src/app

COPY .. .

RUN ls -l
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "./generate_sagas.py"]
CMD ["python", "./run.py"]