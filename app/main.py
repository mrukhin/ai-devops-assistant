from fastapi import FastAPI

app = FastAPI(title="AI-DevOps demo")

@app.get("/")
def root():
    return {"message": "AI-DevOps assistant is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
