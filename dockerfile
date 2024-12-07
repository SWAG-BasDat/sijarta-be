FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

COPY startup.sh .
RUN chmod +x startup.sh

ENV PORT=8080
EXPOSE 8080

CMD ["./startup.sh"]