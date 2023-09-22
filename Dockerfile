FROM continuumio/anaconda3
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN conda install pandas xlrd pip && pip install gtts python-telegram-bot
COPY . /app

WORKDIR /app
CMD ["python", "main.py"]