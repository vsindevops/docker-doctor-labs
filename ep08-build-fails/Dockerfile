FROM python:3.12-slim
WORKDIR /app
# curl, for the health check
RUN apt-get install -y curl
COPY app.py ./
COPY --chmod=755 start.sh ./
ENTRYPOINT ["/app/start.sh"]
