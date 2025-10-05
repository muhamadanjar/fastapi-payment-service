from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from infrastructure.database import db_manager, migration_manager, get_db, setup_from_env
from domain.entity.product import Product

app = FastAPI()