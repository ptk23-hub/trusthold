
def judge_work(brief, delivered_work):
    key = hashlib.sha256(
        (brief + "|" + delivered_work).encode()
    ).hexdigest()

    cache = load_cache()
    if key in cache:
        print("Answered from cache (instant)")
        return cache[key]

    prompt = build_prompt(brief, delivered_work)
    racers = get_racers(prompt)

    if not racers:
        raise RuntimeError("No AI providers configured. Check your .env file.")

    start = time.time()

    with ThreadPoolExecutor(max_workers=len(racers)) as ex:
        futures = {
            ex.submit(fn): name
            for name, fn in racers
        }

        for future in as_completed(futures):
            name = futures[future]

            try:
                res = future.result()
                if valid(res):
                    print(f"{name} won in {time.time()-start:.1f}s")
                    cache[key] = res
                    save_cache(cache)
                    return res

                print(f"{name}: Invalid response: {res}")

            except Exception as e:
                print(f"{name} failed: {type(e).__name__}: {e}")

    raise RuntimeError(
        "All AI providers failed. Your escrow remains on hold."
    )
