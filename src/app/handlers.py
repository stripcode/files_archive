from aiohttp import web
import os
from uuid import uuid4
from time import time
from datetime import datetime
from bson.objectid import ObjectId



fileSizeLimitInBytes = 15 * 1024 * 1024
allowedExtensions = ["png", "jpg", "pdf"]



from json import JSONEncoder

class bb(JSONEncoder):
  def default(self, o):
    if isinstance(o, ObjectId):
      return str(o)
    return JSONEncoder.default(self, o)

dumps = bb().encode


async def getInfoForFiles(request):
  files = []
  filesString = request.query.get('files', "")
  if filesString != "":
    hashes = [ObjectId(hash) for hash in filesString.split(",")]
    async for row in request.mongo.file.find({"_id": {"$in": hashes}}, {"originalFileName": True}):
      files.append(row)
  return web.json_response(files, dumps = dumps)




async def downloadFile(request):
  oid = request.match_info.get('oid')
  row = await request.mongo.file.find_one({"_id": ObjectId(oid)})
  path = os.path.join(request.app["config"]["server"]["upload_dir"], row["filePath"])
  if not os.path.exists(path):
    return web.HTTPNotFound()
  headers = {'CONTENT-DISPOSITION': 'attachment; filename={}'.format(row["originalFileName"])}
  return web.FileResponse(path, headers = headers)



async def uploadFile(request):
  # Принимает файл и складывает его в папку, имя которой строится из даты текущего дня.
  # Файл получает новое имя файла в виде хеша
  # Оригинальное название файла и время заливки хранится в базе.
  # Если файл больше fileSizeLimitInBytes то отсылается 413 коды
  reader = await request.multipart()
  part = await reader.next()
  size = 0 # хранит текущий размер файла после итерации

  # Проверяю что файл подходящего разрешения
  ext = part.filename.split(".")[1]
  if ext not in allowedExtensions:
    return web.HTTPBadRequest(text = "Не разрешенный тип файла")

  # создаю папку дня если не её не существовало
  # и формирую полный путь для сохранения файла
  partFileName = uuid4().hex
  folderDate = datetime.now().strftime("%Y%m")
  folder = os.path.join(request.app["config"]["server"]["upload_dir"], folderDate)
  if not os.path.exists(folder):
    os.mkdir(folder)

  try:
    filename = os.path.join(folder, partFileName)
    with open(filename, 'wb') as file:
      while True:
        chunk = await part.read_chunk()  # 8192 bytes by default.
        if not chunk:
          break
        size += len(chunk)
        if size > fileSizeLimitInBytes:
          raise web.HTTPRequestEntityTooLarge() # 413 http code
        file.write(chunk)

    row = {
      "filePath": os.path.join(folderDate, partFileName),
      "time": time(),
      "originalFileName": part.filename
    }
    result = await request.mongo.file.insert_one(row)
    return web.json_response({
      "id": str(result.inserted_id)
    })
  except Exception as e:
    os.remove(filename)
    return web.HTTPBadRequest(text = "Что пошло не так!") # 400 http code



async def options(request):
  headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
  }
  return web.Response(text = "options", headers = headers)