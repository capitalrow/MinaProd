from __future__ import annotations
import os, requests

class NotionService:
    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN")
        self.base = "https://api.notion.com/v1"
        self.v = "2022-06-28"

    def append_paragraph(self, page_id: str, content: str) -> bool:
        if not self.token: return False
        r = requests.patch(f"{self.base}/blocks/{page_id}/children",
                           headers={"Authorization": f"Bearer {self.token}",
                                    "Notion-Version": self.v,
                                    "Content-Type": "application/json"},
                           json={"children":[{"object":"block","type":"paragraph","paragraph":{"rich_text":[{"type":"text","text":{"content":content}}]}}]})
        return r.status_code in (200, 201)

notion_svc = NotionService()