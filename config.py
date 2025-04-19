class Config:
    # Redis settings
    USE_REDIS = True
    REDIS_HOST = 'localhost'
    REDIS_PORT = 6379
    REDIS_DB = 0
    CACHE_EXPIRY_SECONDS = 900  # 15 minutes

    # Flask settings
    DEBUG = False
    TESTING = False
