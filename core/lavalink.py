import wavelink
from core.config import LAVALINK_NODES

async def connect_lavalink(bot):
    if not wavelink.Pool.nodes:
        nodes = [
            wavelink.Node(uri=n["uri"], password=n["password"])
            for n in LAVALINK_NODES
        ]
        await wavelink.Pool.connect(nodes=nodes, client=bot)

def node_ready():
    return any(
        node.status == wavelink.NodeStatus.CONNECTED
        for node in wavelink.Pool.nodes.values()
    )
