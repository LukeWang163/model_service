FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7

RUN pip install --quiet --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ \
    'pandas==0.25.3' \
    'scikit-learn' \
    'xgboost'

COPY sklxgb /app
COPY prestart.sh /app/prestart.sh