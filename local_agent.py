import sys, json
from router import ModelRouter

def main():
    if len(sys.argv) < 2:
        print("usage: python local_agent.py \"your prompt\" [code]")
        raise SystemExit(1)
    prompt = sys.argv[1]
    tags = {sys.argv[2]} if len(sys.argv) > 2 else set()
    msgs = [{"role":"user","content":prompt}]
    res = ModelRouter().chat(messages=msgs, tags=tags)
    try:
        out = res["choices"][0]["message"]["content"]
    except Exception:
        out = json.dumps(res, indent=2)
    print(out)

if __name__ == "__main__":
    main()
