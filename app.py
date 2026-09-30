
import json, time, uuid
from datetime import datetime
from pathlib import Path
import requests
import streamlit as st

BASE = Path(__file__).parent
DATA = BASE / "data"
DATA.mkdir(exist_ok=True)
HISTORY = DATA / "history.json"
COLLECTIONS = DATA / "collections.json"
ENVIRONMENTS = DATA / "environments.json"

def load_json(path, default):
    if not path.exists():
        path.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def save_json(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def resolve_vars(value, env):
    if not isinstance(value, str):
        return value
    for k, v in env.items():
        value = value.replace("{{" + k + "}}", str(v))
    return value

def parse_kv(text):
    result = {}
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" in line:
            k, v = line.split(":", 1)
            result[k.strip()] = v.strip()
    return result

def pretty_json(value):
    try:
        return json.dumps(value, indent=2, ensure_ascii=False)
    except Exception:
        return str(value)

st.set_page_config(page_title="API Testing Client", page_icon="⚡", layout="wide")

st.markdown("""
<style>
.block-container{padding-top:1.2rem;max-width:1500px}
.hero{padding:20px 24px;border:1px solid rgba(128,128,128,.25);border-radius:18px;margin-bottom:18px}
.hero h1{margin:0;font-size:2.15rem}.muted{opacity:.7}
.metric{padding:14px;border:1px solid rgba(128,128,128,.22);border-radius:14px}
.badge{display:inline-block;padding:4px 10px;border-radius:20px;background:rgba(0,150,136,.12)}
</style>
""", unsafe_allow_html=True)

if "request_url" not in st.session_state:
    st.session_state.request_url = "https://jsonplaceholder.typicode.com/posts/1"
if "method" not in st.session_state:
    st.session_state.method = "GET"
if "headers" not in st.session_state:
    st.session_state.headers = "Accept: application/json"
if "params" not in st.session_state:
    st.session_state.params = ""
if "body" not in st.session_state:
    st.session_state.body = '{\n  "title": "API Testing Client"\n}'
if "response" not in st.session_state:
    st.session_state.response = None

history = load_json(HISTORY, [])
collections = load_json(COLLECTIONS, [])
environments = load_json(ENVIRONMENTS, {
    "Default": {"BASE_URL": "https://jsonplaceholder.typicode.com", "TOKEN": "demo-token"}
})

st.markdown("""
<div class="hero">
<h1>⚡ API Testing Client</h1>
<div class="muted">A Postman-style API testing workspace built with Python + Streamlit</div>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("Workspace")
    env_name = st.selectbox("Environment", list(environments.keys()))
    env = environments[env_name]
    st.caption(f"{len(env)} variables loaded")

    page = st.radio("Navigate", ["Request Builder", "Collections", "History", "Environments", "Import / Export"])
    st.divider()
    st.subheader("Quick examples")
    if st.button("GET Demo"):
        st.session_state.method = "GET"
        st.session_state.request_url = "https://jsonplaceholder.typicode.com/posts/1"
    if st.button("POST Demo"):
        st.session_state.method = "POST"
        st.session_state.request_url = "https://jsonplaceholder.typicode.com/posts"
        st.session_state.body = '{\n  "title": "Hello",\n  "body": "API test",\n  "userId": 1\n}'
    if st.button("Invalid URL Test"):
        st.session_state.request_url = "https://example.invalid/test"
    st.divider()
    st.caption("Tip: use {{VARIABLE}} placeholders in URLs, headers, params, and JSON bodies.")

if page == "Request Builder":
    top = st.columns([1, 4, 1])
    with top[0]:
        method = st.selectbox("Method", ["GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS"], index=["GET","POST","PUT","PATCH","DELETE","HEAD","OPTIONS"].index(st.session_state.method))
        st.session_state.method = method
    with top[1]:
        url = st.text_input("Request URL", st.session_state.request_url)
        st.session_state.request_url = url
    with top[2]:
        timeout = st.number_input("Timeout (s)", 1, 120, 20)

    tabs = st.tabs(["Params", "Headers", "Body", "Auth", "Tests"])

    with tabs[0]:
        st.session_state.params = st.text_area("Query parameters (one per line: key=value)", st.session_state.params, height=150)
    with tabs[1]:
        st.session_state.headers = st.text_area("Headers (one per line: Key: Value)", st.session_state.headers, height=180)
    with tabs[2]:
        body_type = st.selectbox("Body type", ["JSON", "Raw text", "Form data"])
        st.session_state.body = st.text_area("Request body", st.session_state.body, height=220)
    with tabs[3]:
        auth_type = st.selectbox("Authentication", ["None", "Bearer Token", "Basic Auth", "API Key"])
        auth_a = st.text_input("Token / Username / Key", type="default")
        auth_b = st.text_input("Password / Value", type="password")
    with tabs[4]:
        test_script = st.text_area("Simple assertions (optional)", "status == 200\nresponse_time < 2000", height=120)

    c1, c2, c3 = st.columns([1,1,4])
    with c1:
        send = st.button("▶ Send Request", type="primary", use_container_width=True)
    with c2:
        clear = st.button("Clear Response", use_container_width=True)
    if clear:
        st.session_state.response = None

    if send:
        final_url = resolve_vars(st.session_state.request_url, env)
        headers = {k: resolve_vars(v, env) for k,v in parse_kv(st.session_state.headers).items()}
        params = {}
        for line in st.session_state.params.splitlines():
            if "=" in line:
                k,v=line.split("=",1); params[resolve_vars(k.strip(),env)] = resolve_vars(v.strip(),env)

        if auth_type == "Bearer Token" and auth_a:
            headers["Authorization"] = "Bearer " + auth_a
        elif auth_type == "Basic Auth":
            from requests.auth import HTTPBasicAuth
            auth = HTTPBasicAuth(auth_a, auth_b)
        else:
            auth = None
        if auth_type == "API Key" and auth_a:
            headers[auth_a] = auth_b

        payload = None
        if method in ["POST","PUT","PATCH"]:
            if body_type == "JSON":
                try:
                    payload = json.loads(resolve_vars(st.session_state.body, env))
                    headers.setdefault("Content-Type", "application/json")
                except Exception as e:
                    st.error(f"Invalid JSON body: {e}")
                    st.stop()
            elif body_type == "Raw text":
                payload = resolve_vars(st.session_state.body, env)
            else:
                payload = parse_kv(st.session_state.body.replace(":", "="))

        started = time.perf_counter()
        try:
            r = requests.request(method, final_url, params=params, headers=headers, json=payload if isinstance(payload,(dict,list)) else None,
                                  data=payload if isinstance(payload,str) else None, auth=auth, timeout=timeout)
            elapsed = round((time.perf_counter()-started)*1000, 2)
            try: data = r.json()
            except Exception: data = r.text
            result = {
                "id": str(uuid.uuid4()), "timestamp": datetime.now().isoformat(timespec="seconds"),
                "method": method, "url": r.url, "status": r.status_code, "elapsed_ms": elapsed,
                "headers": dict(r.headers), "body": data
            }
            st.session_state.response = result
            history.insert(0, result)
            save_json(HISTORY, history[:100])
        except requests.RequestException as e:
            st.session_state.response = {"error": str(e), "method": method, "url": final_url}
            st.error(f"Request failed: {e}")

    result = st.session_state.response
    if result:
        st.divider()
        if "error" in result:
            st.error(result["error"])
        else:
            status = result["status"]
            a,b,c,d = st.columns(4)
            a.metric("Status", status)
            b.metric("Response Time", f"{result['elapsed_ms']} ms")
            c.metric("Response Size", f"{len(pretty_json(result['body']))} chars")
            d.metric("Headers", len(result["headers"]))
            st.subheader("Response")
            rt1,rt2 = st.tabs(["Body","Headers"])
            with rt1:
                st.code(pretty_json(result["body"]), language="json" if isinstance(result["body"],(dict,list)) else "text")
            with rt2:
                st.json(result["headers"])

elif page == "Collections":
    st.header("Collections")
    with st.form("new_collection"):
        name = st.text_input("Collection name")
        if st.form_submit_button("Create Collection") and name:
            collections.append({"id": str(uuid.uuid4()), "name": name, "requests": []})
            save_json(COLLECTIONS, collections)
            st.success("Collection created.")
    for col in collections:
        with st.expander(f"📁 {col['name']} · {len(col['requests'])} requests"):
            if st.button("Save current request", key=col["id"]):
                col["requests"].append({
                    "name": f"{st.session_state.method} {st.session_state.request_url}",
                    "method": st.session_state.method,
                    "url": st.session_state.request_url,
                    "headers": st.session_state.headers,
                    "body": st.session_state.body
                })
                save_json(COLLECTIONS, collections)
                st.success("Request saved.")
            for i, req in enumerate(col["requests"]):
                st.write(f"**{req['method']}** `{req['url']}`")
                if st.button("Load", key=f"{col['id']}_{i}"):
                    st.session_state.method=req["method"]; st.session_state.request_url=req["url"]
                    st.session_state.headers=req.get("headers",""); st.session_state.body=req.get("body","")
                    st.rerun()

elif page == "History":
    st.header("Request History")
    if st.button("Clear History"):
        history=[]; save_json(HISTORY, history); st.rerun()
    for item in history:
        label=f"{item.get('method','')} · {item.get('status','ERR')} · {item.get('url','')}"
        with st.expander(label):
            st.caption(item.get("timestamp",""))
            st.write(f"Response time: **{item.get('elapsed_ms','-')} ms**")
            if "body" in item: st.code(pretty_json(item["body"]), language="json")
            if st.button("Replay", key=item["id"]):
                st.session_state.method=item["method"]; st.session_state.request_url=item["url"]
                st.rerun()

elif page == "Environments":
    st.header("Environment Manager")
    st.info("Variables are stored locally in data/environments.json. Do not store production secrets in this file.")
    for name, values in environments.items():
        with st.expander(name):
            st.json(values)
    with st.form("env_form"):
        name=st.text_input("Environment name")
        raw=st.text_area("Variables", "BASE_URL=https://example.com\nTOKEN=demo")
        if st.form_submit_button("Add / Update") and name:
            environments[name] = {k:v for k,v in (line.split("=",1) for line in raw.splitlines() if "=" in line)}
            save_json(ENVIRONMENTS,environments)
            st.success("Environment saved.")

elif page == "Import / Export":
    st.header("Import / Export")
    st.subheader("Export current request")
    export = {
        "name": f"{st.session_state.method} Request",
        "method": st.session_state.method,
        "url": st.session_state.request_url,
        "headers": parse_kv(st.session_state.headers),
        "body": st.session_state.body
    }
    st.download_button("Download Request JSON", json.dumps(export,indent=2), "api-request.json", "application/json")
    st.divider()
    st.subheader("Import request JSON")
    uploaded=st.file_uploader("Choose JSON", type=["json"])
    if uploaded:
        try:
            data=json.load(uploaded)
            st.session_state.method=data.get("method","GET")
            st.session_state.request_url=data.get("url","")
            st.session_state.headers="\n".join(f"{k}: {v}" for k,v in data.get("headers",{}).items())
            body=data.get("body","")
            st.session_state.body=body if isinstance(body,str) else json.dumps(body,indent=2)
            st.success("Request imported. Open Request Builder to run it.")
        except Exception as e: st.error(str(e))

st.divider()
st.caption("API Testing Client • Local development tool • Requests are sent directly from the machine running Streamlit.")


