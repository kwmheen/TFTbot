from flask import Flask, request, jsonify, send_from_directory
import os
import subprocess
from datetime import datetime

app = Flask(__name__)
CSV_FILE = 'controlbar.csv'
LIVECAPTURE_DIR = 'livecapture'

# 현재 디렉토리를 기준으로 파일 서빙
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# livecapture 디렉토리 생성
LIVECAPTURE_PATH = os.path.join(BASE_DIR, LIVECAPTURE_DIR)
if not os.path.exists(LIVECAPTURE_PATH):
    os.makedirs(LIVECAPTURE_PATH)

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

@app.route('/livecapture/<path:filename>')
def serve_screenshot(filename):
    # livecapture 폴더의 이미지 파일 서빙
    return send_from_directory(LIVECAPTURE_PATH, filename)

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

@app.route('/api/screenshot', methods=['POST'])
def capture_screenshot():
    try:
        # 현재 datetime을 파일명으로 사용
        now = datetime.now()
        filename = now.strftime('%Y%m%d_%H%M%S_%f.png')
        filepath = os.path.join(LIVECAPTURE_PATH, filename)
        
        # adb exec-out screencap -p 명령 실행
        result = subprocess.run(
            ['adb', 'exec-out', 'screencap', '-p'],
            capture_output=True,
            timeout=10
        )
        
        if result.returncode == 0:
            # 바이너리 데이터를 파일로 저장
            with open(filepath, 'wb') as f:
                f.write(result.stdout)
            
            # 마지막 캡쳐 파일명 저장 (간단한 텍스트 파일로 관리)
            last_screenshot_file = os.path.join(LIVECAPTURE_PATH, '.last_screenshot')
            with open(last_screenshot_file, 'w') as f:
                f.write(filename)
            
            return jsonify({
                'success': True,
                'filename': filename,
                'url': f'/livecapture/{filename}'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'스크린샷 캡쳐 실패: {result.stderr.decode("utf-8", errors="ignore")}'
            }), 400
            
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': '스크린샷 캡쳐 시간 초과'}), 500
    except Exception as e:
        print(f"스크린샷 캡쳐 중 오류 발생: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/last-screenshot', methods=['GET'])
def get_last_screenshot():
    try:
        last_screenshot_file = os.path.join(LIVECAPTURE_PATH, '.last_screenshot')
        if os.path.exists(last_screenshot_file):
            with open(last_screenshot_file, 'r') as f:
                filename = f.read().strip()
            
            filepath = os.path.join(LIVECAPTURE_PATH, filename)
            if os.path.exists(filepath):
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'url': f'/livecapture/{filename}'
                })
        
        return jsonify({
            'success': False,
            'error': '캡쳐된 스크린샷이 없습니다.'
        }), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/delete-all-captures', methods=['POST'])
def delete_all_captures():
    try:
        deleted_count = 0
        if os.path.exists(LIVECAPTURE_PATH):
            # livecapture 폴더 내의 모든 파일 삭제 (.last_screenshot 제외)
            for filename in os.listdir(LIVECAPTURE_PATH):
                filepath = os.path.join(LIVECAPTURE_PATH, filename)
                if os.path.isfile(filepath) and not filename.startswith('.'):
                    try:
                        os.remove(filepath)
                        deleted_count += 1
                    except Exception as e:
                        print(f"파일 삭제 실패 {filename}: {str(e)}")
        
        # .last_screenshot 파일도 삭제
        last_screenshot_file = os.path.join(LIVECAPTURE_PATH, '.last_screenshot')
        if os.path.exists(last_screenshot_file):
            try:
                os.remove(last_screenshot_file)
            except Exception as e:
                print(f".last_screenshot 삭제 실패: {str(e)}")
        
        return jsonify({
            'success': True,
            'message': f'{deleted_count}개의 캡쳐 파일이 삭제되었습니다.',
            'deleted_count': deleted_count
        })
    except Exception as e:
        print(f"캡쳐 파일 삭제 중 오류 발생: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print('서버가 시작되었습니다.')
    print('브라우저에서 http://localhost:5000 을 열어주세요.')
    app.run(debug=True, port=5000)
