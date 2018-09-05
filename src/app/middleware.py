async def mongoMiddleware(app, handler):
  async def middleware(request):
    request.mongo = app.mongoHandler
    response = await handler(request)
    return response
  return middleware