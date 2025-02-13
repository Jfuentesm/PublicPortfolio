# server side
Make sure your existing Python code is set up:

## Example
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.backend.main:app --reload

# front side
Open a separate terminal in src/frontend/:
cd src/frontend
npm install
npm run dev

By default, the front-end dev server is on http://127.0.0.1:3000.


# 3. (Optional) Serving the Front-End from FastAPI

If you want to serve the compiled Vue app directly from FastAPI (so you have a single URL and no CORS concerns), follow these steps:
Build the Vue App
npm run build
This creates a dist/ folder inside src/frontend/.
Serve dist/ as Static Files
In your FastAPI main.py (or a new file), you can do something like:
from fastapi.staticfiles import StaticFiles
import os

## after "app = FastAPI(...)"
app.mount(
    "/",
    StaticFiles(directory=os.path.join("src", "frontend", "dist"), html=True),
    name="frontend"
)
Adjust Host/Port
Now when you run uvicorn, you can open http://127.0.0.1:8000 and see your Vue app.