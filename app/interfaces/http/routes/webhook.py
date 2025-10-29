
from fastapi import APIRouter, Depends
from sqlmodel import Session



router = APIRouter()

@router.post('/{gateway_code}')
def payment(gateway_code):
    return []

@router.post('/test')
def test():
    return []

@router.post('/logs')
def logs():
    return []


@router.post('/{id}/retry')
def webhook_retry(id: str):
    return []