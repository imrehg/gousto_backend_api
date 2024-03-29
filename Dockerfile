FROM python:3.7

WORKDIR /usr/src/app

COPY requirements*.txt ./

RUN pip install -r requirements.txt

COPY *.csv ./
COPY *.py ./
COPY start.sh ./

ENTRYPOINT [ "./start.sh" ]