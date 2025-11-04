echo "PRE-START: starting rq worker..."
/bin/sh -c 'rq worker quizext --url $REDIS_URL' &