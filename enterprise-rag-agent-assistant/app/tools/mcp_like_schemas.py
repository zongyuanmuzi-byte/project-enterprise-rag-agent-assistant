SEARCH_DOCUMENTS_TOOL_SCHEMA = {
    "name": "search_documents",
    "description": "Search indexed documents from the enterprise knowledge base.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "User question or search query.",
            },
            "top_k": {
                "type": "integer",
                "description": "Number of chunks to retrieve.",
                "default": 3,
            },
        },
        "required": ["query"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "results": {
                "type": "array",
                "description": "Retrieved document chunks.",
                "items": {
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "integer",
                            "description": "Source document ID.",
                        },
                        "filename": {
                            "type": "string",
                            "description": "Source filename.",
                        },
                        "chunk_index": {
                            "type": "integer",
                            "description": "Chunk index in the source document.",
                        },
                        "content": {
                            "type": "string",
                            "description": "Retrieved chunk content.",
                        },
                        "distance": {
                            "type": "number",
                            "description": "Vector distance returned by the vector store.",
                        },
                    },
                },
            }
        },
    },
}


MCP_LIKE_TOOL_SCHEMAS = [
    SEARCH_DOCUMENTS_TOOL_SCHEMA,
]