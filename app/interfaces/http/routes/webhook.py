
from fastapi import APIRouter, Depends
from sqlmodel import Session



router = APIRouter()

@router.post('/payment/{gateway_code}')
def payment(gateway_code):
    return []

@router.post('/payment/test')
def test():
    return []

@router.post('/logs')
def logs():
    return []


@router.post('/payment/{id}/retry')
def webhook_retry(id: str):
    return []