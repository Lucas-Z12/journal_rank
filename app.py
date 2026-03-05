# app.py - Flask后端服务
from datetime import datetime

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from algorithm import FIELD_MAP, main
import time

# 创建Flask应用
app = Flask(__name__)
# 允许所有源的请求
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/')
def index():
    """服务主页"""
    return send_from_directory('.', 'index.html')

@app.route('/api/test', methods=['GET'])
def test_api():
    """测试接口"""
    return jsonify({
        'status': 'ok',
        'message': 'API服务运行正常',
        'timestamp': time.time(),
        'version': '2.0.0',
        'fields': list(FIELD_MAP.keys())
    })

@app.route('/api/generate-rankings', methods=['POST'])
def generate_rankings():
    """API接口：根据年份和领域生成排名数据"""
    try:
        # 获取请求参数
        data = request.get_json(silent=True) or {}
        start_year = int(data.get('start_year', 2013))
        end_year = int(data.get('end_year', 2015))
        field = data.get('field', 'economics')
        if field == 'all':
            field = None
        elif isinstance(field, list):
            if 'all' in field:
                field = None
            else:
                invalid_fields = [f for f in field if f not in FIELD_MAP]
                if invalid_fields:
                    return jsonify({
                        'success': False,
                        'error': f"field参数不合法，可选: all, {', '.join(FIELD_MAP.keys())}"
                    }), 400
                if not field:
                    field = None

        if start_year > end_year:
            start_year, end_year = end_year, start_year

        if field is not None and not isinstance(field, list) and field not in FIELD_MAP:
            return jsonify({
                'success': False,
                'error': f"field参数不合法，可选: all, {', '.join(FIELD_MAP.keys())}"
            }), 400

        period = str(start_year) if start_year == end_year else f"{start_year}-{end_year}"
        print(f"📡 收到请求: start_year={start_year}, end_year={end_year}, field={field}, period={period}")
 
        start_time = time.time()

        df, invalid_items, fallback_mode = main(
            start_year=start_year,
            end_year=end_year,
            field=field
        )

        execution_time = round((time.time() - start_time) * 1000, 2)
        metrics = {
            'period': period,
            'field': field or 'all',
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_rows': len(df),
            'fallback_mode': fallback_mode,
            'invalid_count': len(invalid_items),
        }

        response = {
            'success': True,
            'period': period,
            'start_year': start_year,
            'end_year': end_year,
            'field': field or 'all',
            'execution_time': execution_time,
            'columns': list(df.columns),
            'data': df.to_dict('records'),
            'invalid_items': invalid_items,
            'metrics': metrics
        }

        print(f"✅ 响应生成: {len(df)} 条记录, 年份范围 {period}, field={field or 'all'}, 耗时 {execution_time}ms")
        return jsonify(response)

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 启动期刊排名算法API服务...")
    print("📊 访问: http://localhost:5000")
    print("🔗 API端点:")
    print("  - GET  /api/test")
    print("  - POST /api/generate-rankings")
    print("\n📌 首页已绑定 index.html，可直接访问")
    # Windows 环境下开启 reloader 可能触发 WinError 10038
    app.run(debug=True, use_reloader=False, port=5000)