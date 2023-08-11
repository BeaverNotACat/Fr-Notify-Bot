FROM python:3.11.4-alpine3.18
ADD . .
RUN pip install -r requirements.txt
CMD python main.py
