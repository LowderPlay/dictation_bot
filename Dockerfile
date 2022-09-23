FROM continuumio/anaconda3
COPY . /app
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
RUN conda install pandas xlrd pip && pip install gtts python-telegram-bot
RUN touch dict.xls
CMD ["python", "main.py"]