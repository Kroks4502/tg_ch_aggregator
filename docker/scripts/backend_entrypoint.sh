#!/bin/bash

graceful_shutdown() {
    echo "Get signal to shutdown..."
    
    if [ -n "$PYTHON_PID" ]; then
        echo "Sending SIGTERM to Python process (PID: $PYTHON_PID)..."
        kill -TERM "$PYTHON_PID"
        
        for i in {1..30}; do
            if ! kill -0 "$PYTHON_PID" 2>/dev/null; then
                echo "Python process successfully shutdown"
                exit 0
            fi
            sleep 0.1
        done
        
        echo "Process not shutdown, sending SIGKILL..."
        kill -KILL "$PYTHON_PID" 2>/dev/null
    fi
    
    exit 0
}

trap graceful_shutdown SIGTERM SIGINT

echo '🔄 Waiting for database...'
while ! pg_isready -h ${POSTGRES_HOST} -U ${POSTGRES_USER} -d ${POSTGRES_DB}; do
    sleep 2;
done
echo '✅ Database is ready!'

echo '🔄 Applying database migrations...'
yoyo apply --database "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}/${POSTGRES_DB}"
if [ "$?" -ne 0 ]; then
    echo '❌ Database migrations failed!'
    exit 1
fi
echo '✅ Database migrations applied!'

echo '🔄 Waiting for Telegram sessions...'
while [ ! -f /app/sessions/user.session ] || [ ! -f /app/sessions/bot.session ]; do
    echo 'Input authorization parameters into container "create_sessions" use the following command:'
    echo 'docker logs --tail 20 tg_ch_aggregator-create_sessions-1 && docker attach tg_ch_aggregator-create_sessions-1'
    sleep 5;
done
echo '✅ Telegram sessions are ready!'

cd src

echo '🔄 Starting application...'
eval "$@" &
PYTHON_PID=$!

wait "$PYTHON_PID"
