from dotenv import load_dotenv

from app import app

if __name__ == "__main__":
    load_dotenv()
    app.run(debug=True, host="0.0.0.0", port=5000)