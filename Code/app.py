"""
Main Launcher for Automotive Engineering AI Assistant.
Usage:
  python app.py --mode api        # Launches FastAPI backend on port 8000
  python app.py --mode ui         # Launches Streamlit UI on port 8501
  python app.py --mode all        # Launches both services concurrently
"""
import argparse
import subprocess
import sys
import time
from core.config import settings
from database.session import init_db


def main():
    parser = argparse.ArgumentParser(description="Automotive Engineering AI Assistant Launcher")
    parser.add_argument(
        "--mode",
        choices=["api", "ui", "all", "init-db"],
        default="ui",
        help="Run mode: 'api' for FastAPI REST server, 'ui' for Streamlit interface, 'all' for both, 'init-db' to initialize database.",
    )
    args = parser.parse_args()

    # Always ensure DB initialized
    init_db()

    if args.mode == "init-db":
        print("Database initialized successfully.")
        sys.exit(0)

    if args.mode == "api":
        import uvicorn
        print(f"Starting FastAPI backend on http://{settings.API_HOST}:{settings.API_PORT} ...")
        uvicorn.run("backend.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)

    elif args.mode == "ui":
        print(f"Starting Streamlit frontend on port {settings.STREAMLIT_PORT} ...")
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "frontend/streamlit_app.py",
            "--server.port",
            str(settings.STREAMLIT_PORT),
        ]
        subprocess.run(cmd)

    elif args.mode == "all":
        print("Launching both FastAPI and Streamlit services...")
        api_proc = subprocess.Popen([
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            settings.API_HOST,
            "--port",
            str(settings.API_PORT),
        ])
        time.sleep(2)
        ui_proc = subprocess.Popen([
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "frontend/streamlit_app.py",
            "--server.port",
            str(settings.STREAMLIT_PORT),
        ])
        try:
            api_proc.wait()
            ui_proc.wait()
        except KeyboardInterrupt:
            print("\nShutting down services...")
            api_proc.terminate()
            ui_proc.terminate()


if __name__ == "__main__":
    main()
