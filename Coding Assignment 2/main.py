import os
from dotenv import load_dotenv
from supabase import create_client, Client

def get_client() -> Client:
    load_dotenv()  # reads .env in this folder
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in .env")
    return create_client(url, key)

def main():
    sb = get_client()

    # 1) sanity check: first 5 rows
    rows = sb.table("video_games").select("*").limit(5).execute()
    print("\nFirst 5 rows:")
    for r in rows.data:
        print(r)

    # 2) a couple of query examples (optional)
    rpgs = sb.table("video_games").select("title,price").eq("genre", "RPG").order("price", desc=True).execute()
    print("\nRPGs (price desc):")
    for r in rpgs.data:
        print(r)

    new_releases = sb.table("video_games").select("title,release_year").gte("release_year", 2020).order("release_year").execute()
    print("\nReleased 2020 or later:")
    for r in new_releases.data:
        print(r)

if __name__ == "__main__":
    main()
