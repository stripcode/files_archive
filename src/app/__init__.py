from aiohttp import web
import asyncio
from .ext import initMongo
from .middleware import mongoMiddleware
import os
from configparser import ConfigParser
import app.handlers as handlers



def loadConfig(runConfig):
  # загружает дефолтную конфигурацию
  config = ConfigParser()
  with open(os.path.join(os.path.dirname(__file__), 'default.config')) as defaultJsonConfig:
    config.read_file(defaultJsonConfig)

  # загружает файл с продакшена
  if runConfig:
    config.read_file(runConfig)
  return config



async def on_prepare(request, response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"



def createMainApp(config = None):
  loop = asyncio.get_event_loop()
  app = web.Application(middlewares = [mongoMiddleware], loop = loop)
  app["config"] = loadConfig(config)
  app.on_startup.append(initMongo)
  app.on_response_prepare.append(on_prepare)

  # routs
  app.router.add_get("/file/{oid}", handlers.downloadFile)
  app.router.add_get("/file/info/", handlers.getInfoForFiles)
  app.router.add_post("/file/", handlers.uploadFile)
  app.router.add_route("options", "/file/", handlers.options)
  return app