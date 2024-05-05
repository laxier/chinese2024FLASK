FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DATABASE_URL="mysql://root:rootroot@host.docker.internal/blog"

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]