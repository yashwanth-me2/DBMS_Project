import subprocess
import sys
import time
import os

def main():
    print("🏥 Starting Module 18 - Clinical QA System...")
    
    # Ensure we are in the correct directory (module-18 root)
    module_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(module_root)

    # Determine which python executable to use (check for local virtual environment)
    venv_python = os.path.join(module_root, "venv", "bin", "python")
    if os.path.exists(venv_python):
        python_exe = venv_python
    else:
        python_exe = sys.executable

    # Start the FastAPI backend server
    print(f"🚀 Starting FastAPI backend server on port 8000 using {python_exe}...")
    backend_process = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "backend.backend:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    )

    # Give the backend a few seconds to start up and connect to MongoDB
    time.sleep(3)

    # Start the Streamlit frontend server
    print(f"🎨 Starting Streamlit frontend server on port 8501 using {python_exe}...")
    frontend_process = subprocess.Popen(
        [python_exe, "-m", "streamlit", "run", "frontend/frontend.py"]
    )

    try:
        # Wait for both processes (runs indefinitely until interrupted)
        backend_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down servers gracefully...")
        backend_process.terminate()
        frontend_process.terminate()
        backend_process.wait()
        frontend_process.wait()
        print("✅ Servers stopped.")

if __name__ == "__main__":
    main()
