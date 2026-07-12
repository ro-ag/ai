from rulesync import BEGIN, BLOCK, END, upsert_block


def test_creates_block_in_empty_file():
    out = upsert_block("")
    assert out.startswith(BEGIN.split()[0])
    assert BEGIN in out and END in out


def test_appends_after_existing_content():
    out = upsert_block("# My existing rules\n")
    assert out.startswith("# My existing rules")
    assert out.index(BEGIN) > out.index("existing")


def test_idempotent():
    once = upsert_block("# rules\n")
    twice = upsert_block(once)
    assert once == twice


def test_replaces_stale_block_preserving_surroundings():
    stale = f"before\n\n{BEGIN}\nold pointer\n{END}\n\nafter\n"
    out = upsert_block(stale)
    assert "old pointer" not in out
    assert BLOCK in out
    assert out.startswith("before") and out.rstrip().endswith("after")
