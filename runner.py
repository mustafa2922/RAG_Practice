import time
from fatwa_scraper import scrape_fatwas_batch, FatwaDataManager  # <- main module

# ================== CONFIG ====================

# complete URL list
from fatwa_urls import ALL_FATWA_URLS  # You can keep your URLs in a separate file

# Tuning parameters
SAVE_EVERY = 5         # save every N fatwas
DELAY = 0.5            # delay between requests

# ===============================================

def get_resume_index(data_manager, urls):
    """Reads progress.json to determine resume point."""
    progress = data_manager.load_progress()
    processed = progress.get('processed', 0)

    if processed >= len(urls):
        print("✅ All URLs already scraped.")
        return None  # means completed

    print(f"📖 Resuming from index {processed}/{len(urls)}")
    return processed


def main():
    """Main entry point for scraper runner."""
    data_manager = FatwaDataManager()
    start_idx = get_resume_index(data_manager, ALL_FATWA_URLS)

    if start_idx is None:
        return

    print(f"\n🚀 Starting fatwa scraping...")
    start_time = time.time()

    # Run the scraper
    results = scrape_fatwas_batch(
        urls=ALL_FATWA_URLS,
        start_idx=start_idx,
        save_every=SAVE_EVERY,
        delay=DELAY
    )

    elapsed = time.time() - start_time
    print(f"\n✅ Completed in {elapsed/60:.2f} minutes. Total scraped: {len(results)}")


if __name__ == "__main__":
    main()
