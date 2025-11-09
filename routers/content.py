from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import schemas, crud
from database import get_db

router = APIRouter(
    prefix="/microcontent",
    tags=["Microcontent"]
)

@router.get("/", response_model=List[schemas.MicrocontentResponse])
def read_microcontent(
    # --- LÓGICA ACTUALIZADA ---
    # Ahora 'tag' puede ser una lista de strings
    tag: Optional[List[str]] = Query(None), 
    # --- FIN DE LA ACTUALIZACIÓN ---
    db: Session = Depends(get_db)
):
    """
    Obtiene la lista de todos los microcontenidos educativos.
    Opcionalmente, filtra por uno o MÚLTIPLES 'tags'
    (ej. ?tag=ahorro&tag=deuda).
    """
    # Pasamos la lista de tags (o None) directamente a la función crud
    contents = crud.get_microcontent(db=db, tags=tag)
    return contents