#Hyper-V containers have direct access to the Windows file system through a virtual hard disk (VHDX), which can lead to better file system performance compared to WSL. If your application involves frequent file I/O operations, Hyper-V containers may perform better.

FROM python:3.12

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV DATABASE_URL="mysql://root:rootroot@host.docker.internal/blog"
ENV PYTHONUTF8=1

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]