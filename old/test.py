from pathlib import Path

import instaloader
from instaloader import Post, Profile

L = instaloader.Instaloader()
PROJECT_ROOT = Path(__file__).resolve().parent
L.load_session_from_file("valtyry.2016", str(PROJECT_ROOT / "session-valtyry.2016"))

def get_content(shortcode, username=None):
    print(f"Обработка ссылки {shortcode}")
    try:
        post = Post.from_shortcode(L.context, shortcode)
        if username:
            L.download_post(post, target=f"{username}-{shortcode}")
        else:
            L.download_post(post, target=f"{shortcode}")
        print(f"Пост успешно скачан в папку ./{shortcode}/\n")
    except Exception as e:
        print(f"Ошибка при скачивании поста: {e}")

# get_content("DQEJ6OZiKpQ", "buhaitancui1")
profile = Profile.from_username(L.context, "buhaitancui1")
print(profile.get_posts())