import instaloader

L = instaloader.Instaloader()

def get_content(shortcode, username=None):
    print(f"Обработка ссылки {shortcode}")
    try:
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        if username:
            L.download_post(post, target=f"{username}-{shortcode}")
        else:
            L.download_post(post, target=f"{shortcode}")
        print(f"Пост успешно скачан в папку ./{shortcode}/\n")
    except Exception as e:
        print(f"Ошибка при скачивании поста: {e}")