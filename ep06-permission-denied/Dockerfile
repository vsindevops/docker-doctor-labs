FROM python:3.12-alpine
RUN adduser -D app
WORKDIR /app
# keep the settings private
COPY --chmod=600 settings.ini ./
RUN mkdir uploads
COPY app.py ./
# security review: don't run as root
# USER app
CMD ["python", "app.py"]
