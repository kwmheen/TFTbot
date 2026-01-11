from flask import Flask, request, jsonify, send_from_directory
import os

app = Flask(__name__)
CSV_FILE = 'controlbar.csv'

# 현재 디렉토리를 기준으로 파일 서빙
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
    return send_from_directory(BASE_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    # CSS, JS 파일만 서빙
    if filename.endswith(('.css', '.js', '.html')):
        return send_from_directory(BASE_DIR, filename)
    else:
        return "File not found", 404

@app.route('/api/load', methods=['GET'])
def load_csv():
    try:
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, 'r', encoding='utf-8') as f:
                csv_content = f.read()
            return jsonify({'success': True, 'data': csv_content})
        else:
            # 파일이 없으면 기본 헤더만 반환
            return jsonify({'success': True, 'data': '정의된 명령어,adb 명령어\n'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/save', methods=['POST'])
def save_csv():
    try:
        data = request.get_json()
        csv_content = data.get('csvContent', '')
        
        if not csv_content:
            return jsonify({'success': False, 'error': 'CSV content is required'}), 400
        
        with open(CSV_FILE, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        return jsonify({'success': True, 'message': 'CSV file saved successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print('서버가 시작되었습니다.')
    print('브라우저에서 http://localhost:5000 을 열어주세요.')
    app.run(debug=True, port=5000)
