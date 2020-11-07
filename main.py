import uvicorn

if __name__ == "__main__":
    uvicorn.run("src.bibler.biblerAPI:bibler",
                host="localhost", port=8000, reload=True)
