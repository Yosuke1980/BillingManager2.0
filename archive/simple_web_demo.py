#!/usr/bin/env python3
"""
シンプルなWebベースのデモ（Flaskなどの外部ライブラリ不要）
Pythonの標準ライブラリのhttp.serverを使用
"""
import http.server
import socketserver
import json
import sqlite3
import os
import urllib.parse
from datetime import datetime

class BillingWebHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_main_page()
        elif self.path == '/api/payments':
            self.send_payments_data()
        elif self.path == '/api/expenses':
            self.send_expenses_data()
        elif self.path == '/api/masters':
            self.send_masters_data()
        else:
            super().do_GET()
    
    def send_main_page(self):
        html_content = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📻 ラジオ局支払い・費用管理システム</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
        }
        
        .tabs {
            display: flex;
            background: white;
            border-radius: 10px;
            margin-bottom: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .tab {
            flex: 1;
            padding: 1rem;
            background: #f8f9fa;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            font-size: 1rem;
        }
        
        .tab.active {
            background: #007bff;
            color: white;
        }
        
        .tab:hover {
            background: #e9ecef;
        }
        
        .tab.active:hover {
            background: #0056b3;
        }
        
        .content {
            background: white;
            border-radius: 10px;
            padding: 2rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .filters {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }
        
        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        
        .filter-group label {
            font-weight: 600;
            color: #495057;
        }
        
        .filter-group select, .filter-group input {
            padding: 0.5rem;
            border: 1px solid #ced4da;
            border-radius: 5px;
            font-size: 1rem;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        .stat-card {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #007bff;
        }
        
        .stat-card h3 {
            font-size: 2rem;
            color: #007bff;
            margin-bottom: 0.5rem;
        }
        
        .stat-card p {
            color: #6c757d;
            font-weight: 600;
        }
        
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        
        .data-table th,
        .data-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        
        .data-table th {
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
            position: sticky;
            top: 0;
        }
        
        .data-table tr:hover {
            background-color: #f8f9fa;
        }
        
        .status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        
        .status-matched { background-color: #d4edda; color: #155724; }
        .status-processing { background-color: #fff3cd; color: #856404; }
        .status-processed { background-color: #cfe2ff; color: #084298; }
        .status-unprocessed { background-color: #f8f9fa; color: #6c757d; }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: #6c757d;
        }
        
        .table-container {
            overflow-x: auto;
            margin-top: 1rem;
        }
        
        @media (max-width: 768px) {
            .filters {
                flex-direction: column;
            }
            
            .tabs {
                flex-direction: column;
            }
            
            .container {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📻 ラジオ局支払い・費用管理システム</h1>
            <p>Webベース版デモ</p>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('payments')">💳 支払い情報</button>
            <button class="tab" onclick="showTab('expenses')">💰 費用管理</button>
            <button class="tab" onclick="showTab('masters')">⚙️ 費用マスター</button>
        </div>
        
        <div class="content">
            <div id="payments-tab" class="tab-content">
                <h2>💳 支払い情報 (閲覧専用)</h2>
                
                <div class="filters">
                    <div class="filter-group">
                        <label>状態フィルター</label>
                        <select id="status-filter" onchange="filterPayments()">
                            <option value="">すべて</option>
                            <option value="照合済">照合済</option>
                            <option value="処理中">処理中</option>
                            <option value="処理済">処理済</option>
                            <option value="未処理">未処理</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>検索</label>
                        <input type="text" id="search-input" placeholder="件名・支払い先で検索" oninput="filterPayments()">
                    </div>
                </div>
                
                <div class="stats" id="payment-stats">
                    <!-- 統計情報がここに表示される -->
                </div>
                
                <div class="table-container">
                    <table class="data-table" id="payments-table">
                        <thead>
                            <tr>
                                <th>件名</th>
                                <th>案件名</th>
                                <th>支払い先</th>
                                <th>コード</th>
                                <th>金額</th>
                                <th>支払日</th>
                                <th>状態</th>
                            </tr>
                        </thead>
                        <tbody id="payments-tbody">
                            <tr><td colspan="7" class="loading">データを読み込み中...</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div id="expenses-tab" class="tab-content" style="display: none;">
                <h2>💰 費用管理</h2>
                <div class="loading">費用データの表示機能は開発中...</div>
            </div>
            
            <div id="masters-tab" class="tab-content" style="display: none;">
                <h2>⚙️ 費用マスター</h2>
                <div class="loading">マスターデータの表示機能は開発中...</div>
            </div>
        </div>
    </div>

    <script>
        let paymentsData = [];
        
        function showTab(tabName) {
            // タブボタンの状態更新
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            event.target.classList.add('active');
            
            // コンテンツの表示/非表示
            document.querySelectorAll('.tab-content').forEach(content => {
                content.style.display = 'none';
            });
            document.getElementById(tabName + '-tab').style.display = 'block';
            
            // データ読み込み
            if (tabName === 'payments' && paymentsData.length === 0) {
                loadPaymentsData();
            }
        }
        
        async function loadPaymentsData() {
            try {
                const response = await fetch('/api/payments');
                paymentsData = await response.json();
                renderPaymentsTable();
                updatePaymentStats();
            } catch (error) {
                console.error('Error loading payments data:', error);
                document.getElementById('payments-tbody').innerHTML = 
                    '<tr><td colspan="7" style="text-align: center; color: red;">データの読み込みに失敗しました</td></tr>';
            }
        }
        
        function renderPaymentsTable(data = paymentsData) {
            const tbody = document.getElementById('payments-tbody');
            
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">データがありません</td></tr>';
                return;
            }
            
            tbody.innerHTML = data.map(payment => `
                <tr>
                    <td>${payment.subject || ''}</td>
                    <td>${payment.project_name || ''}</td>
                    <td>${payment.payee || ''}</td>
                    <td>${payment.payee_code || ''}</td>
                    <td style="text-align: right;">¥${(payment.amount || 0).toLocaleString()}</td>
                    <td>${payment.payment_date || ''}</td>
                    <td><span class="status status-${getStatusClass(payment.status)}">${payment.status || '未処理'}</span></td>
                </tr>
            `).join('');
        }
        
        function getStatusClass(status) {
            const statusMap = {
                '照合済': 'matched',
                '処理中': 'processing',
                '処理済': 'processed',
                '未処理': 'unprocessed'
            };
            return statusMap[status] || 'unprocessed';
        }
        
        function updatePaymentStats() {
            const stats = {
                total: paymentsData.length,
                matched: paymentsData.filter(p => p.status === '照合済').length,
                processing: paymentsData.filter(p => p.status === '処理中').length,
                processed: paymentsData.filter(p => p.status === '処理済').length,
                unprocessed: paymentsData.filter(p => p.status === '未処理').length
            };
            
            document.getElementById('payment-stats').innerHTML = `
                <div class="stat-card">
                    <h3>${stats.total}</h3>
                    <p>総件数</p>
                </div>
                <div class="stat-card">
                    <h3>${stats.matched}</h3>
                    <p>照合済</p>
                </div>
                <div class="stat-card">
                    <h3>${stats.processing}</h3>
                    <p>処理中</p>
                </div>
                <div class="stat-card">
                    <h3>${stats.unprocessed}</h3>
                    <p>未処理</p>
                </div>
            `;
        }
        
        function filterPayments() {
            const statusFilter = document.getElementById('status-filter').value;
            const searchTerm = document.getElementById('search-input').value.toLowerCase();
            
            const filteredData = paymentsData.filter(payment => {
                const matchesStatus = !statusFilter || payment.status === statusFilter;
                const matchesSearch = !searchTerm || 
                    (payment.subject && payment.subject.toLowerCase().includes(searchTerm)) ||
                    (payment.payee && payment.payee.toLowerCase().includes(searchTerm));
                
                return matchesStatus && matchesSearch;
            });
            
            renderPaymentsTable(filteredData);
        }
        
        // 初期データ読み込み
        loadPaymentsData();
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def send_payments_data(self):
        try:
            conn = sqlite3.connect('billing.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT subject, project_name, payee, payee_code, amount, payment_date, status
                FROM payments
                ORDER BY payment_date DESC
                LIMIT 100
            """)
            rows = cursor.fetchall()
            conn.close()
            
            data = []
            for row in rows:
                data.append({
                    'subject': row[0],
                    'project_name': row[1], 
                    'payee': row[2],
                    'payee_code': row[3],
                    'amount': row[4],
                    'payment_date': row[5],
                    'status': row[6]
                })
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
    
    def send_expenses_data(self):
        # 費用データ（未実装）
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps([]).encode('utf-8'))
    
    def send_masters_data(self):
        # マスターデータ（未実装）
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps([]).encode('utf-8'))

def start_web_server(port=8080):
    """Webサーバーを起動"""
    handler = BillingWebHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"🌐 Webサーバーを起動しました: http://localhost:{port}")
            print("Ctrl+C で停止")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  サーバーを停止しました")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ ポート {port} は既に使用されています。別のポートを試してください。")
            start_web_server(port + 1)
        else:
            print(f"❌ サーバー起動エラー: {e}")

if __name__ == "__main__":
    start_web_server()