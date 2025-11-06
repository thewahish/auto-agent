Agent: Local Hybrid Agent
Goal: If request is coding, generate files and tests then zip. Else, analyze and summarize.
Tags: "code" for repo/APIs/tests/Docker; otherwise general.
Tools: FileWrite, ZipFolder
Routing: local-only via router; no paid APIs.
