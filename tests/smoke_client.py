import asyncio
import os
import sys
from pathlib import Path
from typing import Any
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.types import TextContent


def get_structured(res: Any) -> Any:
    sc = getattr(res, "structuredContent", None)
    if sc is None:
        return None
    if isinstance(sc, dict) and "result" in sc:
        return sc["result"]
    return sc


async def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    cfg = repo_root / "obsidian_mcp_config.yaml"

    cmd = sys.executable
    args = [
        "-c",
        # Run server main directly from source
        "from obsidian_mcp.server import main; main()",
    ]

    env = os.environ.copy()
    # Ensure local 'src' is importable
    src_path = str(repo_root / "src")
    env["PYTHONPATH"] = src_path + (os.pathsep + env["PYTHONPATH"] if "PYTHONPATH" in env and env["PYTHONPATH"] else "")

    if cfg.exists():
        env["OBSIDIAN_MCP_CONFIG"] = str(cfg)

    async with stdio_client(StdioServerParameters(command=cmd, args=args, env=env)) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("TOOLS:", [t.name for t in tools.tools])

            # Create note
            create_res = await session.call_tool("create_note", {
                "title": "Test",
                "content": "# Hello\n\nDemo content from smoke test",
            })
            cs = get_structured(create_res)
            if cs is not None:
                print("CREATE.struct keys:", list(cs.keys()) if isinstance(cs, dict) else type(cs))
            elif create_res.content:
                block = create_res.content[0]
                if isinstance(block, TextContent):
                    print("CREATE.text len:", len(block.text))

            # Read note
            read_res = await session.call_tool("read_note", {
                "title": "Test",
                "include_backlinks": True,
                "include_outlinks": True,
            })
            rs = get_structured(read_res)
            if isinstance(rs, dict):
                print("READ.title:", rs.get("title"), "len:", len(rs.get("content", "")))
            elif read_res.content:
                block = read_res.content[0]
                if isinstance(block, TextContent):
                    print("READ.text len:", len(block.text))

            # List notes
            list_res = await session.call_tool("list_notes", {})
            ls = get_structured(list_res)
            if isinstance(ls, list):
                print("LIST.count:", len(ls))
            elif list_res.content:
                block = list_res.content[0]
                if isinstance(block, TextContent):
                    print("LIST.text len:", len(block.text))


if __name__ == "__main__":
    asyncio.run(main())
