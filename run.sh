#/bin/bash
SUPERVISOR_DIR=/app/lib/${APP_PROJECT_NAME}/supervisor
supervisord -c $SUPERVISOR_DIR/${APP_RUN_NAME}.conf