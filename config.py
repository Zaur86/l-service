from dotenv import load_dotenv
import os

# Загрузка .env файла
load_dotenv()


# Все режимы
class Config:
	EL_PORT = int(os.getenv('EL_PORT'))
	EL_AWS_REGION = os.getenv('EL_AWS_REGION')
	EL_AWS_PROFILE = os.getenv('EL_AWS_PROFILE')
	EL_USE_IAM = bool(int(os.getenv('EL_USE_IAM')))
	EL_DEFAULT_SCROLL = os.getenv('EL_DEFAULT_SCROLL')
	EL_DEFAULT_BATCH_SIZE = os.getenv('EL_DEFAULT_BATCH_SIZE')
	NUM_THREADS = int(os.getenv('NUM_THREADS'))


# Режим разработки
class DevConfig(Config):
	EL_HOST = os.getenv('EL_HOST__DEV')
	DB_URL = os.getenv('DB_URL__DEV')


# Режим тестирования
class TestConfig(Config):
	EL_HOST = os.getenv('EL_HOST__TEST')
	DB_URL = os.getenv('DB_URL__TEST')


# Продакшн
class ProdConfig(Config):
	EL_HOST = os.getenv('EL_HOST__PROD')
	DB_URL = os.getenv('DB_URL__PROD')


config_map = {
	'dev': DevConfig,
	'test': TestConfig,
	'prod': ProdConfig
}
