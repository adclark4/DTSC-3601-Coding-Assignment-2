import os
from dotenv import load_dotenv
from supabase import create_client, Client

def get_client() -> Client:
    # Load environment variables from .env
    load_dotenv()
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    # If either value is missing, stop the program
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in .env")

    # Return a Supabase client we can use to run queries
    return create_client(url, key)

def main():
    # Connect to Supabase
    supabase = get_client()

    # Select all columns from the video_games table, limit results to 5 rows
    response = supabase.table("video_games").select("*").limit(5).execute()

    # Print the rows returned by the query
    print("Rows from video_games:")
    for row in response.data:
        print(row)

if __name__ == "__main__":
    main()
