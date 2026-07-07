def main() -> None:
    import sys
    import os
    import subprocess
    
    # Get the directory of this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(current_dir, "app.py")
    
    # Run streamlit
    cmd = ["streamlit", "run", app_path] + sys.argv[1:]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass

