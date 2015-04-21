web: python -u webapp.py --broker=$RABBITMQ_BIGWIG_TX_URL $WEB_ARGS

worker: celery worker --events --config=webjuice.celery_config --app=webjuice.tasks --loglevel=INFO --broker=$RABBITMQ_BIGWIG_RX_URL

flower: celery flower -A webjuice.tasks --logging=info --broker=$RABBITMQ_BIGWIG_RX_URL --broker_api=$BROKER_API --port=5555

