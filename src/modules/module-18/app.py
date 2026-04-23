import os
import sys

# Ensure module-18 root is on sys.path so all internal imports work
module_root = os.path.dirname(os.path.abspath(__file__))
os.chdir(module_root)
if module_root not in sys.path:
    sys.path.insert(0, module_root)

# Execute the frontend Streamlit app.
# We use exec() instead of import so that Streamlit's rerun mechanism
# works correctly (imports are cached and won't re-execute on rerun).
frontend_path = os.path.join(module_root, "frontend", "frontend.py")
with open(frontend_path) as f:
    code = compile(f.read(), frontend_path, "exec")

# Override __file__ so frontend.py's path-based logic resolves correctly
exec(code, {**globals(), "__file__": frontend_path})
