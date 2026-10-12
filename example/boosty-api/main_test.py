import asyncio
import os
from pathlib import Path

from boosty_api import BoostyApi, BoostyAuthStore, BoostyApiError, BoostyAuthError

BLOG = os.getenv("BOOSTY_BLOG", "").strip()
POST_ID = os.getenv("BOOSTY_POST_ID", "").strip()
DIALOG_ID = os.getenv("BOOSTY_DIALOG_ID", "").strip()

AUTH_PATH = Path(__file__).parent / "secrets" / "boosty_auth.json"

DOWNLOADS = Path(__file__).parent / "downloads"


async def test_posts(api: BoostyApi) -> None:
    print("=== POSTS: GET ===")
    if not BLOG or not POST_ID:
        print("Posts.get skipped: set BOOSTY_BLOG and BOOSTY_POST_ID")
        return

    post = await api.posts.get(BLOG, POST_ID, auth=False)
    print(f"Post: {post.id} {post.title}")

    urls = post.media_urls()
    print(f"Media URLs: {len(urls)}")
    for u in urls[:5]:
        print(" -", u)

    if urls:
        print("=== MEDIA: DOWNLOAD FIRST URL ===")
        DOWNLOADS.mkdir(parents=True, exist_ok=True)
        path = await api.media.download(urls[0], DOWNLOADS / "000.bin")
        print("Saved to:", path)

    print("=== POSTS: LIST (best-effort) ===")
    try:
        data = await api.posts.list(BLOG, limit=5, offset=0, auth=False)
        print("Posts.list raw:", type(data).__name__)
    except Exception as e:
        print("Posts.list skipped (endpoint may differ):", repr(e))


async def test_stats(api: BoostyApi) -> None:
    if not BLOG:
        print("Stats skipped: set BOOSTY_BLOG")
        return

    print("=== STATS: CURRENT ===")
    cur = await api.stats.current(BLOG, auth=True)
    print(cur)

    print("=== STATS: METRICS ===")
    met = await api.stats.metrics(BLOG, auth=True)
    print(met)

    print("=== STATS: DATA ===")
    data = await api.stats.data(BLOG, auth=True)
    print("Keys:", list(data.raw.keys())[:10], "...")
    if "totalMoney" in data.raw and data.raw["totalMoney"]:
        print("totalMoney last:", data.raw["totalMoney"][-1])

    print("=== STATS: EVENTS ===")
    ev = await api.stats.events(BLOG, offset=0, auth=True)
    print("events:", len(ev.data), "extra:", ev.extra)


async def test_subscribers(api: BoostyApi) -> None:
    if not BLOG:
        print("Subscribers skipped: set BOOSTY_BLOG")
        return

    print("=== SUBSCRIBERS: LIST ===")
    page = await api.subscribers.list(BLOG, limit=5, offset=0, auth=True)
    print(f"count={len(page.data)} total={page.total}")
    for s in page.data[:3]:
        print(f" - {s.id} {s.name} status={s.status} price={s.price}")


async def test_sales(api: BoostyApi) -> None:
    if not BLOG:
        print("Sales skipped: set BOOSTY_BLOG")
        return

    print("=== SALES: DONATIONS ===")
    sales = await api.sales.donations(BLOG, limit=5, offset=0, auth=True)
    items = (sales.data.donationsSales if sales.data else [])
    print("donationsSales:", len(items))
    for it in items[:3]:
        print(f" - id={it.id} amount={it.amount} user={getattr(it.user,'name',None)}")


async def test_dialogs(api: BoostyApi) -> None:
    print("=== DIALOGS: LIST ===")
    page = await api.dialogs.list(offset=0, auth=True)
    print("dialogs:", len(page.data), "extra:", page.extra)

    did = int(DIALOG_ID) if DIALOG_ID else (page.data[0].id if page.data else None)
    if not did:
        print("No dialog id available; skipping dialog detail/send.")
        return

    print("=== DIALOGS: GET ===")
    detail = await api.dialogs.get(did, auth=True)
    msg_count = len(detail.messages.data) if detail.messages else 0
    print(f"Dialog {detail.id} chatmate={getattr(detail.chatmate,'name',None)} messages={msg_count}")

    print("=== DIALOGS: SEND TEXT ===")
    sent = await api.dialogs.send_text(did, "Dear user, thx for donations!", auth=True)
    print(f"Sent message id={sent.id} createdAt={sent.createdAt}")


async def main() -> None:
    auth_store = BoostyAuthStore(AUTH_PATH)
    auth = auth_store.load()

    async with BoostyApi(auth=auth, auth_store=auth_store, refresh_path="/oauth/token") as api:
        # If access token is expired, try refresh early
        try:
            if api.auth.refresh_token and api.auth.will_expire_within(5):
                print("=== AUTH: PRE-REFRESH ===")
                await api.refresh()
                print("refreshed; expires_at=", api.auth.expires_at)
        except Exception as e:
            print("Refresh skipped/failed:", repr(e))

        # Public endpoints
        await test_posts(api)

        # Auth endpoints
        for fn in (test_stats, test_subscribers, test_dialogs, test_sales):
            try:
                await fn(api)
            except (BoostyAuthError, BoostyApiError) as e:
                print(f"{fn.__name__} failed:", repr(e))

    print("DONE")


if __name__ == "__main__":
    asyncio.run(main())
