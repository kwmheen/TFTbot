from flask import Flask, request, jsonify, send_from_directory
import os
import subprocess

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

@app.route('/api/execute', methods=['POST'])
def execute_adb():
    try:
        data = request.get_json()
        adb_command = data.get('command', '')
        
        if not adb_command:
            return jsonify({'success': False, 'error': 'ADB command is required'}), 400
        
        # adb 명령어를 리스트로 분리 (공백 기준)
        command_parts = adb_command.split()
        
        # subprocess로 실행
        result = subprocess.run(
            command_parts,
            capture_output=True,
            text=True,
            timeout=30  # 30초 타임아웃
        )
        
        output = result.stdout if result.stdout else result.stderr
        
        if result.returncode == 0:
            print(f"ADB 명령어 실행 성공: {adb_command}")
            print(f"출력: {output}")
            return jsonify({
                'success': True,
                'message': 'ADB 명령어가 성공적으로 실행되었습니다.',
                'output': output
            })
        else:
            print(f"ADB 명령어 실행 실패: {adb_command}")
            print(f"에러: {output}")
            return jsonify({
                'success': False,
                'error': f'ADB 명령어 실행 실패: {output}',
                'output': output
            }), 400
            
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': '명령어 실행 시간 초과'}), 500
    except Exception as e:
        print(f"ADB 명령어 실행 중 오류 발생: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print('서버가 시작되었습니다.')
    print('브라우저에서 http://localhost:5000 을 열어주세요.')
    app.run(debug=True, port=5000)
