import motor.motor_asyncio



def initMongo(app):
  client = motor.motor_asyncio.AsyncIOMotorClient(app["config"]["mongo"]["dsn"])
  app.mongoHandler = client[app["config"]["mongo"]["database"]]