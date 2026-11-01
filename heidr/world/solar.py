from heidr import net
from heidr.contracts import Key, Material
from heidr.registry import world

DISCUSSION = "https://services.swpc.noaa.gov/text/discussion.txt"
INDEX = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"


def available(ctx) -> bool:
    return ctx.has("net")


def paragraphs(discussion: str) -> list[str]:
    kept = "\n".join(line for line in discussion.splitlines() if not line.startswith((":", "#")))
    found = []
    for block in kept.split("\n\n"):
        # A label such as ".Forecast..." opens a paragraph, and a section title
        # such as "Solar Wind" is a block with no sentence in it.
        lines = [line for line in block.splitlines() if not line.startswith(".")]
        paragraph = " ".join(" ".join(lines).split())
        if paragraph.endswith("."):
            found.append(paragraph)
    return found


@world(
    "solar",
    needs=("net",),
    visual="plasma",
    defaults={"discussion": DISCUSSION, "index": INDEX, "timeout": 10},
)
def run(ctx, key: Key) -> Material:
    found = paragraphs(net.fetch_text(ctx.settings["discussion"], timeout=ctx.settings["timeout"]))
    if not found:
        return Material("", (), "swpc", {"paragraphs": 0})

    latest = net.fetch_json(ctx.settings["index"], timeout=ctx.settings["timeout"])[-1]

    ctx.emit("stage", f"solar kp {latest['Kp']}")
    return Material(
        # The forecast stands for hours, so the key picks a paragraph of it and
        # two questions in one afternoon can still be told different things.
        text=found[key.seed % len(found)],
        numbers=(round(latest["Kp"] * 100), latest["a_running"]),
        source="swpc",
        extra={"kp": latest["Kp"], "measured": latest["time_tag"], "paragraphs": len(found)},
    )
