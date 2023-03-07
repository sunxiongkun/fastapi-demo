import os

from src.utils.log import update_logging_config

env_key = "DEPLOY_APP_ENV"
deploy_env = os.getenv(env_key, "local")

configuration_dict = {
    "local": {
        "pic_web_mysql": {
            "host": "localhost",
            "port": 3325,
            "username": "global_algorithm_user",
            "password": "123456",
            "database": "global_algorithm",
        },
        "pic_web_redis": {
            "host": "localhost",
            "port": 6380,
            "password": 'pass777',
        },
        "logging_config": {
            "level": "DEBUG",
        },
    }
}

current_env_config = configuration_dict[deploy_env]
logging_config = current_env_config.get("logging_config", {})
logging_config['level'] = os.getenv('RESET_LOGGING_LEVEL') or logging_config.get("level")
# update_logging_config(logging_config)

# redis
is_redis_keepalive = not os.getenv('OFF_REDIS_KEEPALIVE', False)
pic_web_redis = {
    **current_env_config['pic_web_redis'],
    "socket_keepalive": is_redis_keepalive,
    "health_check_interval": 0.1 if is_redis_keepalive else 0,
    "retry_on_timeout": True,
    "socket_timeout": 0.5,
    "socket_connect_timeout": 0.5,
}

# mysql
pic_web_mysql = current_env_config["pic_web_mysql"]
