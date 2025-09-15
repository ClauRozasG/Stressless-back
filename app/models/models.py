from datetime import date, datetime
from sqlmodel import Relationship, SQLModel, Field
from typing import List, Optional
from app.models.base import Base



class LiderColaborador(SQLModel, table=True):
    __tablename__ = "lidercolaborador"  
    _table_args_ = {"schema": "public"}  
    id: Optional[int] = Field(default=None, primary_key=True)
    id_lider: int = Field(foreign_key="lider.id")
    id_colaborador: Optional[int] = Field(default=None, foreign_key="colaborador.id")
    estado:str
    id_invitacion:int = Field(foreign_key="invitacion.id")
    fecha_inicio:date
    fecha_fin:date

    lider: Optional["Lider"] = Relationship(back_populates="colaboradores_link")
    colaborador: Optional["Colaborador"] = Relationship(back_populates="lideres_link")
    invitacion: Optional["Invitacion"] = Relationship(back_populates="lider_colaborador_link")

class Lider(SQLModel, table=True):
    __tablename__ = "lider"  
    _table_args_ = {"schema": "public"}  
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    correo: str
    contrasenia: str
    estado: bool

    colaboradores_link: List[LiderColaborador] = Relationship(back_populates="lider")

class PreColaborador(SQLModel, table=True):
    __tablename__ = "precolaborador"
    _table_args_ = {"schema": "public"}  
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    correo: str
    correo_lider: str

    invitacion_precolaborador_link: List["Invitacion"] = Relationship(back_populates="precolaborador")

class Invitacion(SQLModel, table=True):
    __tablename__ = "invitacion"  
    _table_args_ = {"schema": "public"}  
    id:Optional[int] = Field(default=None, primary_key=True)
    id_precolaborador:int = Field(foreign_key="precolaborador.id")
    fecha_envio:date
    fecha_respuesta:date
    estado:bool
    codigo:str

    lider_colaborador_link: List[LiderColaborador] = Relationship(back_populates="invitacion")
    precolaborador: Optional[PreColaborador] = Relationship(back_populates="invitacion_precolaborador_link")


class Notificacion(SQLModel, table=True):
    __tablename__ = "notificacion"
    _table_args_ = {"schema": "public"}
    id: Optional[int] = Field(default=None, primary_key=True)
    id_colaborador: int = Field(foreign_key="colaborador.id")
    id_prueba: int = Field(foreign_key="prueba.id")
    mensaje: str = "Tienes una nueva prueba pendiente"
    leido: bool = False

    prueba: Optional["Prueba"] = Relationship(back_populates="notificacion_prueba_link")


class NotificacionLider(SQLModel, table=True):
    __tablename__ = "notificacion_lider"
    _table_args_ = {"schema": "public"}

    id: Optional[int] = Field(default=None, primary_key=True)
    id_lider: int = Field(foreign_key="lider.id")
    id_colaborador: int = Field(foreign_key="colaborador.id")
    consecutivas: int = 0
    mensaje: str = "El colaborador presenta resultados consecutivos de estrés"
    creado_en: datetime = Field(default_factory=datetime.utcnow)
    leido: bool = False



class Prueba(SQLModel, table=True):
    __tablename__ = "prueba"
    _table_args_ = {"schema": "public"}
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_registro: date
    fecha_resultado: Optional[date] = None
    id_colaborador: int = Field(foreign_key="colaborador.id")
    estado: int  # 0 = pendiente, 1 = en proceso, 2 = completada
    resultado: Optional[bool] = None

    colaborador: Optional["Colaborador"] = Relationship(back_populates="prueba_colaborador_link")
    notificacion_prueba_link: List["Notificacion"] = Relationship(back_populates="prueba")

    class Config:
        orm_mode = True

class Colaborador(SQLModel, table=True):
    __tablename__ = "colaborador"  
    _table_args_ = {"schema": "public"}  
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
    _table_args_ = {"schema": "public"}
    id: Optional[int] = Field(default=None, primary_key=True)
    id_colaborador: int = Field(foreign_key="colaborador.id")
    id_prueba: int = Field(foreign_key="prueba.id")  
    resultado: str
    fecha: datetime = Field(default_factory=datetime.utcnow)
    archivo_audio: str



class ResetContrasena(SQLModel, table=True):
    __tablename__ = "reset_contrasena"
    _table_args_ = {"schema": "public"}
    id: Optional[int] = Field(default=None, primary_key=True)
    correo: str
    rol: str  
    codigo: str  # OTP de 6 dígitos
    expira_en: datetime
    usado: bool = False
    creado_en: datetime = Field(default_factory=datetime.utcnow)

class AgendaPrueba(SQLModel, table=True):
    __tablename__ = "agenda_prueba"
    _table_args_ = {"schema": "public"}

    id: Optional[int] = Field(default=None, primary_key=True)
    id_lider: int = Field(foreign_key="lider.id")
    id_colaborador: int = Field(foreign_key="colaborador.id")

    # 
    scheduled_at: datetime

    estado: int = 0            # 0=queued, 1=dispatched, 2=cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None

