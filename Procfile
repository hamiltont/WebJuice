web: python -u webapp.py --redis=$REDISCLOUD_URL $WEB_ARGS

worker: celery worker --events --config=webjuice.celery_config --app=webjuice.tasks --loglevel=INFO --broker=$REDISCLOUD_URL
