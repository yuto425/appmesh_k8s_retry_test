FROM python:3.7

RUN pip3 install Flask==1.0.2
RUN pip3 install gunicorn==19.7.1
ADD app.py app.py
ADD config.py config.py
CMD ["gunicorn", "--config", "config.py", "app:app"]