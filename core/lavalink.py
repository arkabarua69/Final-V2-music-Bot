import wavelink
from core.config import LAVALINK_NODES


async def connect_lavalink(bot):
    """
    Lavalink connection (Wavelink v2 & v3 compatible)
    """

    # Prevent double connection
    if wavelink.Pool.nodes:
        return

    nodes = []
    for node in LAVALINK_NODES:
        nodes.append(
            wavelink.Node(
                uri=node["uri"],
                password=node["password"],
            )
        )

    await wavelink.Pool.connect(
        client=bot,
        nodes=nodes,
    )

    print("✅ Lavalink connected")


def node_ready() -> bool:
    """
    Check if at least one Lavalink node is connected
    """
    return any(
        node.status == wavelink.NodeStatus.CONNECTED
        for node in wavelink.Pool.nodes.values()
    )
