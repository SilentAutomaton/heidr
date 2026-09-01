from heidr.contracts import Material
from heidr.registry import reading


@reading("mute", visual="hush")
def run(ctx, question: str, material: Material):
    # The oracle keeps its mouth shut. The material is already on screen, and
    # the silence is the reading.
    return
    yield
