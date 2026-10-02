from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ledgerlens.ask import answer

app = FastAPI(title="LedgerLens")


class Question(BaseModel):
    question: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(body: Question):
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question must not be empty")
    return answer(question)
