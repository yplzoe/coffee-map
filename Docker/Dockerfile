FROM apache/airflow:2.9.0-python3.9
COPY requirements.txt /requirements.txt
# RUN pip install --user --upgrade pip
# RUN pip install --no-cache-dir --user -r /requirements.txt # --no-cache-dir good practise when installing packages using pip. It helps to keep the image lightweight
RUN pip install --no-cache-dir -r /requirements.txt
