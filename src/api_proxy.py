#!/usr/bin/env python3
"""
API 代理服务 - 前端在线查询后端
===============================
提供 /api/proxy 端点，转发前端查询请求到 RedFox API。
解决前端 CORS 问题和 API Key 安全问题。

用法:
    python src/api_proxy.py --port 5173

配置 systemd 服务:
    [Unit]
    Description=AI Hot Radar API Proxy
    After=network.target

    [Service]
    Type=simple
    User=www
    WorkingDirectory=/home/www/aihot
    Environment=REDFOX_API_KEY=ak_your_key
    ExecStart=/usr/bin/python3 src/api_proxy.py --port 5173
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target
"""
import os
import json
import argparse
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

REDFOX_BASE = "https://redfox.hk/story/api"
TIMEOUT = 30

# 允许的端点白名单
ALLOWED_ENDPOINTS = {
    "gzhData/searchArticle",
    "gzhData/searchAccount",
    "gzhData/queryArticleList",
    "gzhData/queryArticle",
    "gzhData/queryAccount",
    "dyData/queryWork",
    "dyData/queryAccount",
    "xhsData/queryWork",
    "xhsData/queryAccount",
}


class ProxyHandler(BaseHTTPRequestHandler):
    """API 代理请求处理器"""

    def do_OPTIONS(self):
        """CORS 预检"""
        self._set_cors()
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        """转发 API 请求"""
        parsed = urlparse(self.path)

        if parsed.path != "/api/proxy":
            self._send_error(404, {"error": "未找到"})
            return

        # 读取请求体
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            req_data = json.loads(body)
        except json.JSONDecodeError:
            self._send_error(400, {"error": "JSON 解析失败"})
            return

        endpoint = req_data.get("endpoint", "")
        params = req_data.get("params", {})

        # 端点白名单校验
        if endpoint not in ALLOWED_ENDPOINTS:
            self._send_error(403, {"error": f"端点 {endpoint} 不在白名单中"})
            return

        # 转发到 RedFox API
        result = self._proxy_request(endpoint, params)
        self._send_json(result)

    def _proxy_request(self, endpoint: str, body: dict) -> dict:
        """实际转发请求到 RedFox API"""
        api_key = os.getenv("REDFOX_API_KEY", "")

        url = f"{REDFOX_BASE}/{endpoint}"
        data = json.dumps(body).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "X-API-KEY": api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return {"code": e.code, "msg": str(e), "data": None}
        except Exception as e:
            return {"code": -1, "msg": str(e), "data": None}

    def _set_cors(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _send_json(self, data: dict):
        self._set_cors()
        resp = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.wfile.write(resp)

    def _send_error(self, status: int, data: dict):
        self.send_response(status)
        self._set_cors()
        resp = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.wfile.write(resp)

    def log_message(self, format, *args):
        """简化日志输出"""
        print(f"[API Proxy] {args[0]}")


def main():
    parser = argparse.ArgumentParser(description="AI 热点雷达 API 代理服务")
    parser.add_argument("--port", type=int, default=5173, help="监听端口")
    parser.add_argument("--host", default="127.0.0.1", help="监听地址")
    args = parser.parse_args()

    api_key = os.getenv("REDFOX_API_KEY")
    if not api_key:
        print("⚠️ REDFOX_API_KEY 未设置，代理将无法正常调用 RedFox API")

    server = HTTPServer((args.host, args.port), ProxyHandler)
    print(f"🚀 API 代理服务已启动: http://{args.host}:{args.port}/api/proxy")
    print(f"   允许的端点: {len(ALLOWED_ENDPOINTS)} 个")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        server.shutdown()


if __name__ == "__main__":
    main()
