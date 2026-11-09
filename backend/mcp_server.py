"""
BRANDVAULT AI — Model Context Protocol (MCP) server  (Round 3 · Improvement 2)

Lets AI assistants and IDEs (Claude Desktop, Claude Code, Cursor, …) use
BrandVault's governance checks over the standard MCP protocol (JSON-RPC over
stdio). It is a thin client of BrandVault's public API, so it works against a
local or deployed instance and never touches the database directly.

Security
- Authenticates with an organisation API key (created by an Administrator in
  Settings → API keys). Every call is scoped to that organisation.
- Every tool is read-only. There is deliberately no tool to approve, publish or
  change Brand DNA — agents advise, humans decide.

Setup
    pip install "mcp>=2.3" httpx
    set BRANDVAULT_URL=https://brandvault-ai.onrender.com      (default: http://127.0.0.1:8000)
    set BRANDVAULT_API_KEY=bv_...
    python backend/mcp_server.py            # stdio transport

Claude Desktop / Claude Code config example:
    {"mcpServers": {"brandvault": {"command": "python", "args": ["backend/mcp_server.py"],
      "env": {"BRANDVAULT_URL": "https://...", "BRANDVAULT_API_KEY": "bv_..."}}}}
"""
from __future__ import annotations

import os
import sys
from typing import Any, Dict, List, Optional

import httpx

BASE = os.getenv("BRANDVAULT_URL", "http://127.0.0.1:8000").rstrip("/") + "/api/v1/public"
KEY = os.getenv("BRANDVAULT_API_KEY", "")
TIMEOUT = float(os.getenv("BRANDVAULT_TIMEOUT", "90"))  # free hosts can take ~60s to wake up


class BrandVaultError(RuntimeError):
    pass


def _call(method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if not KEY:
        raise BrandVaultError("Set BRANDVAULT_API_KEY (Settings → API keys in BrandVault).")
    r = httpx.request(method, BASE + path, json=body, headers={"X-API-Key": KEY}, timeout=TIMEOUT)
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail")
        except ValueError:
            detail = r.text[:200]
        raise BrandVaultError(f"BrandVault returned {r.status_code}: {detail}")
    return r.json()


# ------------------------------- tool functions --------------------------------
# Plain functions (testable without MCP); registered as MCP tools below.
def get_brand_profile() -> Dict[str, Any]:
    """Approved products, facts (with sources) and terminology for this organisation."""
    return _call("GET", "/brand")


def search_brand_guidelines(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """Search the organisation's approved guideline passages; results include page citations."""
    return _call("POST", "/search", {"query": query, "top_k": top_k})["results"]


def check_copy(text: str, channels: Optional[List[str]] = None, region: Optional[str] = None) -> Dict[str, Any]:
    """Check marketing copy against Brand DNA, approved facts, channel rules and required disclaimers.
    Nothing is saved; the result is advice for a human."""
    return _call("POST", "/check", {"text": text, "channels": channels or [], "region": region, "persist": False})


def check_publish_gate(text: str, reference: Optional[str] = None) -> Dict[str, Any]:
    """Is this exact copy approved for publishing (matches a current Brand Passport)?
    The check is recorded in BrandVault's append-only integrity log."""
    return _call("POST", "/gate", {"text": text, "reference": reference})


def get_review_status(submission_id: str) -> Dict[str, Any]:
    """Review status, score and Brand Passport of a submission."""
    return _call("GET", f"/submissions/{submission_id}")


TOOLS = [get_brand_profile, search_brand_guidelines, check_copy, check_publish_gate, get_review_status]


def build_server():
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations

    server = MCPServer(name="brandvault", title="BrandVault AI",
                       instructions="Brand governance checks for marketing copy. All tools are read-only; "
                                    "only an authorised person can approve or publish in BrandVault.")
    read_only = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
    for fn in TOOLS:
        server.tool(annotations=read_only)(fn)
    return server


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        print("Tools:", ", ".join(f.__name__ for f in TOOLS))
        print("Brand:", get_brand_profile().get("organization"))
        sys.exit(0)
    build_server().run("stdio")
