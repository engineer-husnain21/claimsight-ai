"""Split policy markdown documents into one chunk per rule section."""

import re

from app.schemas.policy_chunk import PolicyChunk

DOCUMENT_TITLE_PATTERN = re.compile(r"^#\s+(.+)$")
RULE_HEADING_PATTERN = re.compile(r"^##\s+([A-Z]+-\d+)\s+(.+)$")


class PolicyChunkingService:
    """Turn a policy document into chunks, one per `## CODE Title` section."""

    def split_document(self, source: str, text: str) -> list[PolicyChunk]:
        """Return one chunk per rule section, skipping sections with no body."""
        document_title = source
        chunks: list[PolicyChunk] = []
        current_code: str | None = None
        current_title = ""
        body_lines: list[str] = []

        def flush() -> None:
            body = "\n".join(body_lines).strip()
            if current_code is not None and body:
                chunks.append(
                    PolicyChunk(
                        id=f"{source}:{current_code}",
                        source=source,
                        rule_code=current_code,
                        title=current_title,
                        text=f"{document_title} - {current_code} {current_title}\n{body}",
                    )
                )

        for line in text.splitlines():
            rule_match = RULE_HEADING_PATTERN.match(line.strip())
            if rule_match:
                flush()
                current_code, current_title = rule_match.group(1), rule_match.group(2)
                body_lines = []
                continue

            title_match = DOCUMENT_TITLE_PATTERN.match(line.strip())
            if title_match and current_code is None:
                document_title = title_match.group(1)
                continue

            if current_code is not None:
                body_lines.append(line)

        flush()
        return chunks
