from datetime import date, datetime
from sqlmodel import Relationship, SQLModel, Field
from typing import List, Optional
from app.models.base import Base

class LiderColaborador(SQLModel, table=True):
    _tablename_ = "lidercolaborador"  # nombre de la tabla en minúsculas
    _table_args_ = {"schema": "public"}  # esquema en PostgreSQL
    id_lider:int = Field(foreign_key="lider.id",primary_key=True)
    id_colaborador:int = Field(foreign_key="colaborador.id",primary_key=True)
    estado:str
    id_invitacion:int = Field(foreign_key="invitacion.id")
    fecha_inicio:date
    fecha_fin:date

    lider: Optional["Lider"] = Relationship(back_populates="colaboradores_link")
    colaborador: Optional["Colaborador"] = Relationship(back_populates="lideres_link")
    invitacion: Optional["Invitacion"] = Relationship(back_populates="lider_colaborador_link")

class Lider(SQLModel, table=True):
    _tablename_ = "lider"  # nombre de la tabla en minúsculas
    _table_args_ = {"schema": "public"}  # esquema en PostgreSQL
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    correo: str
    contrasenia: str
    estado: bool

    colaboradores_link: List[LiderColaborador] = Relationship(back_populates="lider")

class PreColaborador(SQLModel, table=True):
    __tablename__ = "precolaborador"
    _table_args_ = {"schema": "public"}  # esquema en PostgreSQL
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    correo: str
    correo_lider: str

    invitacion_precolaborador_link: List["Invitacion"] = Relationship(back_populates="precolaborador")

class Invitacion(SQLModel, table=True):
    _tablename_ = "invitacion"  # nombre de la tabla en minúsculas
    _table_args_ = {"schema": "public"}  # esquema en PostgreSQL
    id:Optional[int] = Field(default=None, primary_key=True)
    id_precolaborador:int = Field(foreign_key="precolaborador.id")
    fecha_envio:date
    fecha_respuesta:date
    estado:bool
    codigo:str

    lider_colaborador_link: List[LiderColaborador] = Relationship(back_populates="invitacion")
    precolaborador: Optional[PreColaborador] = Relationship(back_populates="invitacion_precolaborador_link")

class Notificacion(SQLModel, table=True):
    _tablename_ = "notificacion"
    _table_args = {"schema": "public"} 
    id: Optional[int] = Field(default=None, primary_key=True)
    descripcion:str
    estado:str
    fecha_envio:date
    id_prueba:int = Field(foreign_key="prueba.id")

    prueba:Optional["Prueba"] = Relationship(back_populates="notificacion_prueba_link")

    class Config:
        orm_mode = True

class Prueba(SQLModel, table=True):
    _tablename_ = "prueba" #nombre de la tabla en minúscula
    _table_args_ = {"schema": "public"} # esquema en PostgreSQL
    id:Optional[int] = Field(default=None, primary_key=True)
    fecha_registro:date
    fecha_resultado:date
    id_colaborador:int = Field(foreign_key="colaborador.id")
    estado:int
    resultado:bool

    colaborador: Optional["Colaborador"] = Relationship(back_populates="prueba_colaborador_link")
    notificacion_prueba_link: List[Notificacion] = Relationship(back_populates="prueba")

    class Config:
        orm_mode = True

class Colaborador(SQLModel, table=True):
    _tablename_ = "colaborador"  # nombre de la tabla en minúsculas
    _table_args_ = {"schema": "public"}  # esquema en PostgreSQL
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    correo: str
    contrasenia: str
    estado:bool

    lideres_link: List[LiderColaborador] = Relationship(back_populates="colaborador")
    prueba_colaborador_link: List[Prueba] = Relationship(back_populates="colaborador")
    # Tabla PreColaborador

class ResultadoAnalisis(SQLModel, table=True):
    __tablename__ = "resultado_analisis"
    id: Optional[int] = Field(default=None, primary_key=True)
    id_colaborador: int = Field(foreign_key="colaborador.id")
    resultado: str
    fecha: datetime = Field(default_factory=datetime.utcnow)
    archivo_audio: str  

