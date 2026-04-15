from fastapi import Request, HTTPException

# Clave administrador global
ADMIN_KEY = "Curtits2026!"


def validar_admin(request: Request):
    """
    Valida la clave de administrador desde query params
    Raise HTTPException 403 si la clave es incorrecta
    """
    key = request.query_params.get("admin_key")
    
    if not key or key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Acceso no autorizado. Clave de administrador incorrecta.")
