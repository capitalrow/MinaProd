import os
from __init__ import create_app

app = create_app()

if __name__ == "__main__":
    # Prefer PORT env or default 5000
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
