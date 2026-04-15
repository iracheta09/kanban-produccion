from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routers import menu, area_detalle, catalogo, catalogo_areas, kanban, productividad, reporte_diario

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

# Servir archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(menu.router)
app.include_router(area_detalle.router)
app.include_router(catalogo.router)
app.include_router(catalogo_areas.router)
app.include_router(kanban.router)
app.include_router(productividad.router)
app.include_router(reporte_diario.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Manejador personalizado para excepciones HTTP
    Muestra página de acceso denegado para 403
    """
    if exc.status_code == 403:
        return templates.TemplateResponse(
            "acceso_denegado.html",
            {"request": request},
            status_code=403
        )
    # Para otras excepciones, usar el comportamiento por defecto
    raise exc