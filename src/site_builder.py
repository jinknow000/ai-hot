"""
静态站点生成器 - 数据嵌入 HTML
=============================
将采集数据和分析结果嵌入 HTML 模板，输出到 dist/ 目录。
- dist/index.html: 主页面
- dist/data/latest.json: 最新数据
- dist/archive/YYYY-MM-DD.json: 历史归档
"""
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional


class SiteBuilder:
    """静态站点生成器"""

    def __init__(self, dist_dir: str = "dist", template_dir: str = "templates"):
        self.dist_dir = Path(dist_dir)
        self.template_dir = Path(template_dir)
        self.data_dir = self.dist_dir / "data"
        self.archive_dir = self.data_dir / "archive"

    def build(self, site_data: dict, date: Optional[str] = None) -> str:
        """
        构建静态站点

        Args:
            site_data: 完整的站点数据 (采集 + 分析)
            date: 日期字符串 YYYY-MM-DD

        Returns:
            生成的 index.html 路径
        """
        date = date or datetime.now().strftime("%Y-%m-%d")
        site_data["meta"] = site_data.get("meta", {})
        site_data["meta"]["buildTime"] = datetime.now().isoformat()
        site_data["meta"]["version"] = "1.0.0"

        # 1. 保存数据文件
        self._save_data(site_data, date)

        # 2. 生成 HTML
        html = self._generate_html(site_data)

        index_path = self.dist_dir / "index.html"
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(html, encoding="utf-8")

        return str(index_path)

    def _save_data(self, site_data: dict, date: str):
        """保存 JSON 数据文件"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # 最新数据
        latest_path = self.data_dir / "latest.json"
        latest_path.write_text(
            json.dumps(site_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        # 归档
        archive_path = self.archive_dir / f"{date}.json"
        archive_path.write_text(
            json.dumps(site_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _generate_html(self, site_data: dict) -> str:
        """生成 HTML 页面"""
        # 尝试使用模板
        template_path = self.template_dir / "index.html"
        if template_path.exists():
            template = template_path.read_text(encoding="utf-8")
        else:
            template = self._default_template()

        # 嵌入数据
        data_json = json.dumps(site_data, ensure_ascii=False)

        # 替换数据占位符
        html = template.replace(
            "{{SITE_DATA}}", data_json
        ).replace(
            "{{BUILD_TIME}}", site_data.get("meta", {}).get("buildTime", "")
        ).replace(
            "{{DATE}}", site_data.get("date", "")
        )

        return html

    def _default_template(self) -> str:
        """内置默认 HTML 模板"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI 热点雷达 - 每日 AI 热点聚合</title>
    <meta name="description" content="每日自动聚合抖音、小红书、公众号三大平台 AI 热点，LLM 结构化分析与机会评分">
    <style>
        :root {
            --bg: #0f1117;
            --card-bg: #1a1d28;
            --border: #2a2d3a;
            --text: #e1e4ea;
            --text-secondary: #8b8fa3;
            --accent: #6c5ce7;
            --accent-glow: rgba(108, 92, 231, 0.3);
            --douyin: #ff2d55;
            --xhs: #ff5a5f;
            --wechat: #07c160;
            --gold: #f0c040;
            --radius: 12px;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Microsoft YaHei", sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            min-height: 100vh;
        }

        .container { max-width: 1200px; margin: 0 auto; padding: 0 24px; }

        /* Header */
        .header {
            padding: 48px 0 32px;
            text-align: center;
            border-bottom: 1px solid var(--border);
            margin-bottom: 40px;
        }
        .header h1 {
            font-size: 2.5rem;
            font-weight: 800;
            background: linear-gradient(135deg, #6c5ce7, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
        }
        .header .subtitle { color: var(--text-secondary); font-size: 1.05rem; }
        .header .date-badge {
            display: inline-block;
            margin-top: 12px;
            padding: 4px 16px;
            border-radius: 20px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        /* Stats Bar */
        .stats-bar {
            display: flex;
            gap: 16px;
            margin-bottom: 40px;
            flex-wrap: wrap;
        }
        .stat-card {
            flex: 1;
            min-width: 160px;
            padding: 20px;
            border-radius: var(--radius);
            background: var(--card-bg);
            border: 1px solid var(--border);
            text-align: center;
        }
        .stat-card .number {
            font-size: 2rem;
            font-weight: 700;
            background: linear-gradient(135deg, #6c5ce7, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .stat-card .label { color: var(--text-secondary); font-size: 0.85rem; margin-top: 4px; }

        /* Section */
        .section { margin-bottom: 48px; }
        .section-title {
            font-size: 1.4rem;
            font-weight: 700;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .section-title .icon { font-size: 1.5rem; }

        /* Daily Summary */
        .summary-card {
            padding: 24px;
            border-radius: var(--radius);
            background: var(--card-bg);
            border: 1px solid var(--border);
            margin-bottom: 20px;
        }
        .summary-card .overview {
            color: var(--text);
            line-height: 1.8;
        }
        .hot-topics {
            display: flex;
            gap: 8px;
            margin-top: 16px;
            flex-wrap: wrap;
        }
        .hot-topic-tag {
            padding: 4px 14px;
            border-radius: 20px;
            background: rgba(108, 92, 231, 0.15);
            color: #a78bfa;
            font-size: 0.85rem;
        }

        /* Top Picks */
        .pick-card {
            padding: 20px;
            border-radius: var(--radius);
            background: var(--card-bg);
            border: 1px solid var(--border);
            margin-bottom: 16px;
            position: relative;
            transition: border-color 0.2s;
        }
        .pick-card:hover { border-color: var(--accent); }
        .pick-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 12px;
            margin-bottom: 12px;
        }
        .pick-title {
            font-size: 1.1rem;
            font-weight: 600;
            flex: 1;
        }
        .pick-title a {
            color: var(--text);
            text-decoration: none;
        }
        .pick-title a:hover { color: #a78bfa; }
        .score-badge {
            flex-shrink: 0;
            width: 48px;
            height: 48px;
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 1.2rem;
            background: linear-gradient(135deg, #6c5ce7, #a78bfa);
            color: #fff;
        }
        .score-badge.high { background: linear-gradient(135deg, #f0c040, #ff8c00); }
        .pick-meta {
            display: flex;
            gap: 16px;
            flex-wrap: wrap;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }
        .platform-tag {
            padding: 2px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .platform-tag.douyin { background: rgba(255,45,85,0.2); color: var(--douyin); }
        .platform-tag.xiaohongshu { background: rgba(255,90,95,0.2); color: var(--xhs); }
        .platform-tag.wechat { background: rgba(7,193,96,0.2); color: var(--wechat); }
        .pick-detail { margin-top: 12px; }
        .pick-detail .label-text { color: var(--text-secondary); font-size: 0.8rem; }
        .pick-detail .content-text { margin-bottom: 8px; font-size: 0.9rem; }

        /* Platform Panel */
        .platform-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
            gap: 20px;
        }
        .platform-panel {
            border-radius: var(--radius);
            overflow: hidden;
            border: 1px solid var(--border);
        }
        .platform-panel .panel-header {
            padding: 16px 20px;
            font-weight: 700;
            font-size: 1.05rem;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .platform-panel.douyin .panel-header { background: rgba(255,45,85,0.1); color: var(--douyin); }
        .platform-panel.xiaohongshu .panel-header { background: rgba(255,90,95,0.1); color: var(--xhs); }
        .platform-panel.wechat .panel-header { background: rgba(7,193,96,0.1); color: var(--wechat); }
        .platform-panel .panel-body { padding: 16px 20px; background: var(--card-bg); }
        .panel-item {
            padding: 12px 0;
            border-bottom: 1px solid var(--border);
        }
        .panel-item:last-child { border-bottom: none; }
        .panel-item .item-title {
            font-weight: 600;
            margin-bottom: 6px;
        }
        .panel-item .item-title a { color: var(--text); text-decoration: none; }
        .panel-item .item-title a:hover { color: #a78bfa; }
        .panel-item .item-meta {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            font-size: 0.8rem;
            color: var(--text-secondary);
        }
        .panel-item .item-meta span {
            display: flex;
            align-items: center;
            gap: 3px;
        }

        /* Insights */
        .insight-card {
            padding: 20px;
            border-radius: var(--radius);
            background: var(--card-bg);
            border: 1px solid var(--border);
            margin-bottom: 12px;
        }
        .insight-card h4 { margin-bottom: 8px; }
        .insight-card p { color: var(--text-secondary); font-size: 0.9rem; }

        /* Query Cards */
        .query-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 16px;
        }
        .query-card {
            padding: 20px;
            border-radius: var(--radius);
            background: var(--card-bg);
            border: 1px solid var(--border);
        }
        .query-card h4 { margin-bottom: 12px; font-size: 0.95rem; }
        .query-card input {
            width: 100%;
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid var(--border);
            background: var(--bg);
            color: var(--text);
            font-size: 0.9rem;
            margin-bottom: 8px;
        }
        .query-card button {
            width: 100%;
            padding: 8px 16px;
            border-radius: 8px;
            border: none;
            background: var(--accent);
            color: #fff;
            font-size: 0.9rem;
            cursor: pointer;
            font-weight: 600;
        }
        .query-card button:hover { opacity: 0.9; }
        .query-result {
            margin-top: 12px;
            max-height: 300px;
            overflow-y: auto;
            font-size: 0.8rem;
            background: var(--bg);
            padding: 12px;
            border-radius: 8px;
            white-space: pre-wrap;
            color: var(--text-secondary);
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 40px 0;
            color: var(--text-secondary);
            font-size: 0.85rem;
            border-top: 1px solid var(--border);
            margin-top: 60px;
        }
        .footer a { color: #a78bfa; text-decoration: none; }

        /* Loading */
        .loading { text-align: center; padding: 48px; color: var(--text-secondary); }

        /* Responsive */
        @media (max-width: 768px) {
            .header h1 { font-size: 1.8rem; }
            .stats-bar { gap: 8px; }
            .stat-card { min-width: 130px; padding: 14px; }
            .stat-card .number { font-size: 1.5rem; }
            .platform-grid { grid-template-columns: 1fr; }
            .query-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <h1>🔭 AI 热点雷达</h1>
            <p class="subtitle">每日自动聚合抖音·小红书·公众号 AI 热点，LLM 结构化分析与机会评分</p>
            <div class="date-badge" id="dateBadge">加载中...</div>
        </header>

        <!-- Stats Bar -->
        <div class="stats-bar" id="statsBar">
            <div class="stat-card">
                <div class="number" id="statDouyin">-</div>
                <div class="label">🎵 抖音样本</div>
            </div>
            <div class="stat-card">
                <div class="number" id="statXhs">-</div>
                <div class="label">📕 小红书灵感</div>
            </div>
            <div class="stat-card">
                <div class="number" id="statWechat">-</div>
                <div class="label">💬 公众号爆文</div>
            </div>
            <div class="stat-card">
                <div class="number" id="statPicks">-</div>
                <div class="label">⭐ Agent 推荐</div>
            </div>
        </div>

        <!-- Daily Summary -->
        <section class="section" id="summarySection">
            <div class="section-title"><span class="icon">📊</span> 每日摘要</div>
            <div class="summary-card">
                <div class="overview" id="summaryOverview">加载中...</div>
                <div class="hot-topics" id="hotTopics"></div>
            </div>
        </section>

        <!-- Top Picks -->
        <section class="section" id="topPicksSection">
            <div class="section-title"><span class="icon">⭐</span> Agent 精选推荐</div>
            <div id="topPicksList"></div>
        </section>

        <!-- Platform Data -->
        <section class="section" id="platformSection">
            <div class="section-title"><span class="icon">📡</span> 三平台数据面板</div>
            <div class="platform-grid" id="platformGrid"></div>
        </section>

        <!-- Insights -->
        <section class="section" id="insightsSection">
            <div class="section-title"><span class="icon">💡</span> 平台洞察</div>
            <div id="insightsList"></div>
        </section>

        <!-- Content Angles & Risks -->
        <section class="section" id="anglesSection">
            <div class="section-title"><span class="icon">🎯</span> 内容角度 & 风险提醒</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;" id="anglesGrid"></div>
        </section>

        <!-- Online Query -->
        <section class="section" id="querySection">
            <div class="section-title"><span class="icon">🔍</span> 在线查询 (RedFox API)</div>
            <div class="query-grid" id="queryGrid"></div>
        </section>

        <!-- Footer -->
        <footer class="footer">
            <p>Powered by <a href="https://redfox.hk" target="_blank">红狐数据 API</a> · LLM 结构化分析 · GitHub Actions 每日自动构建</p>
            <p style="margin-top: 4px;">数据更新时间: <span id="buildTime">-</span></p>
        </footer>
    </div>

    <script>
        // 站点数据 (构建时嵌入)
        const SITE_DATA = {{SITE_DATA}};

        // ========== 渲染引擎 ==========

        function init() {
            if (!SITE_DATA || !SITE_DATA.date) {
                document.body.innerHTML = '<div class="loading">⚠️ 暂无数据，请稍后再来</div>';
                return;
            }

            renderHeader();
            renderStats();
            renderSummary();
            renderTopPicks();
            renderPlatforms();
            renderInsights();
            renderAngles();
            renderQueryCards();
        }

        function renderHeader() {
            document.getElementById('dateBadge').textContent = '📅 ' + SITE_DATA.date;
            document.getElementById('buildTime').textContent =
                SITE_DATA.meta?.buildTime || '-';
        }

        function renderStats() {
            const platforms = SITE_DATA.platforms || {};
            document.getElementById('statDouyin').textContent =
                (platforms.douyin?.sampleSize || 0) + ' 条';
            document.getElementById('statXhs').textContent =
                (platforms.xiaohongshu?.sampleSize || 0) + ' 条';
            document.getElementById('statWechat').textContent =
                (platforms.wechat?.sampleSize || 0) + ' 条';
            const picks = SITE_DATA.analysis?.topPicks || [];
            document.getElementById('statPicks').textContent = picks.length + ' 条';
        }

        function renderSummary() {
            const summary = SITE_DATA.analysis?.dailySummary || {};
            document.getElementById('summaryOverview').textContent =
                summary.overview || '暂无摘要';

            const topicsDiv = document.getElementById('hotTopics');
            topicsDiv.innerHTML = (summary.hotTopics || []).map(t =>
                `<span class="hot-topic-tag">#${escapeHtml(t)}</span>`
            ).join('');
        }

        function renderTopPicks() {
            const picks = SITE_DATA.analysis?.topPicks || [];
            const container = document.getElementById('topPicksList');

            if (!picks.length) {
                container.innerHTML = '<div class="summary-card">暂无精选推荐</div>';
                return;
            }

            container.innerHTML = picks.map((pick, i) => {
                const scoreClass = pick.opportunityScore >= 80 ? 'high' : '';
                const platformClass = pick.platform === 'douyin' ? 'douyin' :
                    pick.platform === 'xiaohongshu' ? 'xiaohongshu' : 'wechat';
                const platformName = pick.platform === 'douyin' ? '抖音' :
                    pick.platform === 'xiaohongshu' ? '小红书' : '公众号';

                return `
                <div class="pick-card">
                    <div class="pick-header">
                        <div class="pick-title">
                            <a href="${escapeHtml(pick.url || '#')}" target="_blank" rel="noopener">
                                ${i + 1}. ${escapeHtml(pick.title || '无标题')}
                            </a>
                        </div>
                        <div class="score-badge ${scoreClass}">${pick.opportunityScore || '-'}</div>
                    </div>
                    <div class="pick-meta">
                        <span class="platform-tag ${platformClass}">${platformName}</span>
                        ${pick.reason ? `<span>📌 ${escapeHtml(pick.reason)}</span>` : ''}
                    </div>
                    ${pick.contentAngle ? `
                    <div class="pick-detail">
                        <div class="label-text">💡 内容角度</div>
                        <div class="content-text">${escapeHtml(pick.contentAngle)}</div>
                    </div>` : ''}
                    ${pick.riskNote ? `
                    <div class="pick-detail">
                        <div class="label-text">⚠️ 风险提示</div>
                        <div class="content-text">${escapeHtml(pick.riskNote)}</div>
                    </div>` : ''}
                </div>`;
            }).join('');
        }

        function renderPlatforms() {
            const platforms = SITE_DATA.platforms || {};
            const grid = document.getElementById('platformGrid');
            const configs = [
                { key: 'douyin', name: '🎵 抖音样本', cls: 'douyin' },
                { key: 'xiaohongshu', name: '📕 小红书灵感', cls: 'xiaohongshu' },
                { key: 'wechat', name: '💬 公众号爆文', cls: 'wechat' },
            ];

            grid.innerHTML = configs.map(cfg => {
                const data = platforms[cfg.key] || {};
                const items = data.items || [];

                return `
                <div class="platform-panel ${cfg.cls}">
                    <div class="panel-header">${cfg.name} (${items.length} 条)</div>
                    <div class="panel-body">
                        ${items.length ? items.map(item => renderPlatformItem(item, cfg.key)).join('') : '<p style="color:var(--text-secondary);padding:12px 0;">暂无数据</p>'}
                    </div>
                </div>`;
            }).join('');
        }

        function renderPlatformItem(item, platform) {
            const metaItems = [];
            if (item.readCount) metaItems.push(`👁 ${formatNum(item.readCount)}`);
            if (item.likeCount) metaItems.push(`👍 ${formatNum(item.likeCount)}`);
            if (item.wowCount) metaItems.push(`👀 ${formatNum(item.wowCount)}`);
            if (item.commentCount) metaItems.push(`💬 ${formatNum(item.commentCount)}`);
            if (item.shareCount) metaItems.push(`🔄 ${formatNum(item.shareCount)}`);
            if (item.collectCount) metaItems.push(`⭐ ${formatNum(item.collectCount)}`);

            return `
            <div class="panel-item">
                <div class="item-title">
                    <a href="${escapeHtml(item.workUrl || '#')}" target="_blank" rel="noopener">
                        ${escapeHtml(item.title || '无标题')}
                    </a>
                </div>
                <div class="item-meta">
                    ${item.author ? `<span>✍️ ${escapeHtml(item.author)}</span>` : ''}
                    ${metaItems.join('')}
                </div>
            </div>`;
        }

        function renderInsights() {
            const insights = SITE_DATA.analysis?.platformInsights || {};
            const container = document.getElementById('insightsList');
            const labels = { douyin: '🎵 抖音', xiaohongshu: '📕 小红书', wechat: '💬 公众号' };

            container.innerHTML = Object.entries(insights).map(([key, val]) => `
                <div class="insight-card">
                    <h4>${labels[key] || key}</h4>
                    <p>${escapeHtml(val)}</p>
                </div>
            `).join('');
        }

        function renderAngles() {
            const angles = SITE_DATA.analysis?.contentAngles || [];
            const risks = SITE_DATA.analysis?.riskNotes || [];
            const grid = document.getElementById('anglesGrid');

            grid.innerHTML = `
                <div class="summary-card">
                    <h4 style="margin-bottom:12px;">🎯 内容切入角度</h4>
                    <ul style="padding-left:20px;color:var(--text-secondary);">
                        ${angles.map(a => `<li style="margin-bottom:6px;">${escapeHtml(a)}</li>`).join('')}
                    </ul>
                </div>
                <div class="summary-card">
                    <h4 style="margin-bottom:12px;">⚠️ 风险提醒</h4>
                    <ul style="padding-left:20px;color:var(--text-secondary);">
                        ${risks.map(r => `<li style="margin-bottom:6px;">${escapeHtml(r)}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        function renderQueryCards() {
            const cards = [
                { title: '🔍 搜索公众号文章', endpoint: 'gzhData/searchArticle', fields: ['关键词'], body: (v) => ({ keyword: v[0], offset: 0, sortType: '_4' }) },
                { title: '🔍 搜索公众号', endpoint: 'gzhData/searchAccount', fields: ['公众号名称'], body: (v) => ({ name: v[0] }) },
                { title: '📋 查询文章列表', endpoint: 'gzhData/queryArticleList', fields: ['公众号名称'], body: (v) => ({ name: v[0], offset: 0, count: 10 }) },
                { title: '📄 查询文章详情', endpoint: 'gzhData/queryArticle', fields: ['文章 URL'], body: (v) => ({ workUrl: v[0] }) },
                { title: '📡 查询公众号信息', endpoint: 'gzhData/queryAccount', fields: ['公众号 ID'], body: (v) => ({ accountId: v[0] }) },
                { title: '🎵 抖音作品详情', endpoint: 'dyData/queryWork', fields: ['作品 ID'], body: (v) => ({ workId: v[0] }) },
                { title: '🎵 抖音账号详情', endpoint: 'dyData/queryAccount', fields: ['账号 ID'], body: (v) => ({ accountId: v[0] }) },
                { title: '📕 小红书作品详情', endpoint: 'xhsData/queryWork', fields: ['作品 ID'], body: (v) => ({ workId: v[0] }) },
                { title: '📕 小红书账号详情', endpoint: 'xhsData/queryAccount', fields: ['账号 ID'], body: (v) => ({ accountId: v[0] }) },
            ];

            document.getElementById('queryGrid').innerHTML = cards.map((card, idx) => `
                <div class="query-card">
                    <h4>${card.title}</h4>
                    ${card.fields.map((f, fi) => `<input type="text" id="q${idx}_f${fi}" placeholder="${f}">`).join('')}
                    <button onclick="doQuery(${idx})">查询</button>
                    <div class="query-result" id="qResult${idx}" style="display:none;"></div>
                </div>
            `).join('');

            // 存储卡片配置
            window._queryCards = cards;
        }

        async function doQuery(idx) {
            const card = window._queryCards[idx];
            const resultDiv = document.getElementById('qResult' + idx);
            resultDiv.style.display = 'block';
            resultDiv.textContent = '查询中...';

            const values = card.fields.map((_, fi) =>
                document.getElementById('q' + idx + '_f' + fi).value
            );
            if (values.some(v => !v.trim())) {
                resultDiv.textContent = '⚠️ 请填写所有参数';
                return;
            }

            // 注意: 在线查询需要后端代理，前端不能直接调 RedFox API (CORS + API Key 安全)
            resultDiv.textContent = '⚠️ 此功能需要部署后端 API 代理 (/api/proxy)。' +
                '\\n请参考项目 README 配置 Nginx 反向代理和 Python API 代理服务。' +
                '\\n\\n查询参数:\\n' + JSON.stringify(card.body(values), null, 2);
        }

        // ========== 工具函数 ==========
        function formatNum(n) {
            if (!n) return '0';
            if (n >= 10000) return (n / 10000).toFixed(1) + 'w';
            if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
            return String(n);
        }

        function escapeHtml(str) {
            if (!str) return '';
            const div = document.createElement('div');
            div.textContent = str;
            return div.innerHTML;
        }

        // 启动
        document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>'''
