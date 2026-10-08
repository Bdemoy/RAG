from datetime import datetime

from sqlmodel import Field,SQLModel

class Category(SQLModel,table=True):
    __tablename__ = 'categories'

    id:int | None=Field(default=None,primary_key=True)#插入后才有id
    name:str=Field(unique=True)
    created_at:datetime = Field(default=datetime.now)


