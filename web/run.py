from dotenv import load_dotenv

from app_web import app

if __name__ == "__main__":
    load_dotenv()
    app.run(debug=True, host="0.0.0.0", port=5000)