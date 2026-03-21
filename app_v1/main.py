from fastapi import FastAPI
import uvicorn




def create_app() -> FastAPI:
    app = FastAPI()
    return app

def print_routes(app: FastAPI) -> None:
    print("Registered Routes:")
    for route in app.routes:
        print(f"Path: {getattr(route, 'path')}, Methods: {getattr(route, 'methods')}")

app = create_app()
print_routes(app)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008, reload=False)