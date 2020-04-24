# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

#
# This file is included in the final Docker image and SHOULD be overridden when
# deploying the image to prod. Settings configured here are intended for use in local
# development environments. Also note that superset_config_docker.py is imported
# as a final step as a means to override "defaults" configured here
#

import logging
import os
from celery.schedules import crontab

from werkzeug.contrib.cache import FileSystemCache


logger = logging.getLogger()


def get_env_variable(var_name, default=None):
    """Get the environment variable or raise exception."""
    try:
        return os.environ[var_name]
    except KeyError:
        if default is not None:
            return default
        else:
            error_msg = "The environment variable {} was missing, abort...".format(
                var_name
            )
            raise EnvironmentError(error_msg)


DATABASE_DIALECT = get_env_variable("DATABASE_DIALECT")
DATABASE_USER = get_env_variable("DATABASE_USER")
DATABASE_PASSWORD = get_env_variable("DATABASE_PASSWORD")
DATABASE_HOST = get_env_variable("DATABASE_HOST")
DATABASE_PORT = get_env_variable("DATABASE_PORT")
DATABASE_DB = get_env_variable("DATABASE_DB")

# The SQLAlchemy connection string.
SQLALCHEMY_DATABASE_URI = "%s://%s:%s@%s:%s/%s" % (
    DATABASE_DIALECT,
    DATABASE_USER,
    DATABASE_PASSWORD,
    DATABASE_HOST,
    DATABASE_PORT,
    DATABASE_DB,
)

REDIS_HOST = get_env_variable("REDIS_HOST")
REDIS_PORT = get_env_variable("REDIS_PORT")

LOG_LEVEL = "ERROR"

class CeleryConfig(object):
    BROKER_URL = "redis://%s:%s/0" % (REDIS_HOST, REDIS_PORT)
    CELERY_IMPORTS = (
        'superset.sql_lab',
        'superset.tasks',
    )
    CELERY_RESULT_BACKEND = "redis://%s:%s/1" % (REDIS_HOST, REDIS_PORT)
    CELERYD_LOG_LEVEL = 'ERROR'
    CELERYD_PREFETCH_MULTIPLIER = 10
    CELERY_ACKS_LATE = True
    CELERY_ANNOTATIONS = {
        'sql_lab.get_sql_results': {
            'rate_limit': '100/s',
        },
        'email_reports.send': {
            'rate_limit': '1/s',
            'time_limit': 120,
            'soft_time_limit': 150,
            'ignore_result': True,
        },
    }
    CELERYBEAT_SCHEDULE = {
        'email_reports.schedule_hourly': {
            'task': 'email_reports.schedule_hourly',
            'schedule': crontab(minute='*', hour='*'),
        },
    }


CELERY_CONFIG = CeleryConfig

EMAIL_REPORTS_WEBDRIVER = 'firefox'
WEBDRIVER_CONFIGURATION  = { "service_log_path": "/tmp/webvdriver.log",
#        "executable_path": "/usr/bin/chromedriver"
        }

WEBDRIVER_BASEURL = "http://superset:8088/"

# options = webdriver.ChromeOptions()
# options.binary_location = r"<YOUR_CHROME_PATH>\chrome.exe"
# chrome_driver_path = r"<PATH_TO_CHROME_DRIVER>\chromedriver.exe>"
# 
# browser = webdriver.Chrome(chrome_driver_path, chrome_options=options)

ENABLE_SCHEDULED_EMAIL_REPORTS = True
EMAIL_NOTIFICATIONS = True

EMAIL_REPORTS_USER = 'admin'

SMTP_HOST = "ip-172-31-8-185"
SMTP_STARTTLS = False
SMTP_SSL = False
SMTP_USER = ""
SMTP_PORT = 25
SMTP_PASSWORD = ""
SMTP_MAIL_FROM = "superset@RDday"

# https://superset.incubator.apache.org/installation.html#caching
CACHE_CONFIG = {
  'CACHE_TYPE': 'redis',
  'CACHE_DEFAULT_TIMEOUT': 5 * 60,
  'CACHE_KEY_PREFIX':'superset_results',
  'CACHE_REDIS_URL': 'redis://%s:%s/0' % (REDIS_HOST, REDIS_PORT),
}


# On Redis
from werkzeug.contrib.cache import RedisCache
RESULTS_BACKEND = RedisCache(
    host='%s' % REDIS_HOST, port='%s' % REDIS_PORT, key_prefix='superset_results')


#
# Optionally import superset_config_docker.py (which will have been included on
# the PYTHONPATH) in order to allow for local settings to be overridden
#
try:
    from superset_config_docker import *  # noqa
    import superset_config_docker

    logger.info(
        f"Loaded your Docker configuration at " f"[{superset_config_docker.__file__}]"
    )
except ImportError:
    logger.info("Using default Docker config...")
