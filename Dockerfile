FROM python:3.12.3

WORKDIR /bothub-platform

COPY platform/requirements.txt /bothub-platform/platform/requirements.txt

RUN pip install --no-cache-dir -r platform/requirements.txt

COPY platform/ /bothub-platform/platform/
COPY utils/ /bothub-platform/utils
COPY hub/ /bothub-platform/hub

CMD ["python", "platform/splatform.py"]