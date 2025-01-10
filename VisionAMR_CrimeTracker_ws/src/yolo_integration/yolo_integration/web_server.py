import rclpy
from rclpy.node import Node
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import threading
import base64
from std_msgs.msg import String
import re
import sqlite3
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '1234'  
login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

class WebServer(Node):
    def __init__(self):
        super().__init__('web_server')
        self.bridge = CvBridge()
        self.latest_image = None
        self.latest_rviz_image = None  # RViz2 화면 저장 변수
        self.alerts = []
        self.amr_state = "초기 위치"  # AMR 상태 변수

        # ROS2 토픽 구독 설정
        self.subscription = self.create_subscription(
            Image,
            'detected_image',
            self.image_callback,
            10
        )
        self.subscription_alarm = self.create_subscription(
            String,
            'system_status',
            self.alarm_callback,
            10
        )
        self.subscription_amr_state = self.create_subscription(
            String,
            'amr_state',  # AMR 상태를 퍼블리시하는 토픽
            self.amr_state_callback,
            10
        )

    def image_callback(self, msg):
        self.latest_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')

    def alarm_callback(self, msg):
        match = re.search(r"(\d+) : ([\d-]+\s[\d:]+)", msg.data)
        if match:
            object_id_num = match.group(1)
            detection_time = match.group(2)
            alert_message = f"Object ID: {object_id_num}, Time: {detection_time}"
            self.get_logger().info(f"Alarm received: {alert_message}")
            self.alerts.append(alert_message)
            print(f"Updated alarm list: {self.alerts}")

    def amr_state_callback(self, msg):
        self.amr_state = msg.data
        self.get_logger().info(f"AMR 상태 업데이트: {self.amr_state}")

# 데이터베이스에서 감지된 객체 정보를 가져오는 함수
def get_detected_objects():
    conn = sqlite3.connect('/home/hyuna/지능_2/detections.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM detections')
    rows = cursor.fetchall()
    conn.close()
    # 행을 사전 리스트로 변환
    objects = []
    for row in rows:
        objects.append({
            'id': row[0],
            'class_name': row[1],
            'confidence': row[2],
            'x': row[3],
            'y': row[4],
            'timestamp': row[5],
            'objectid': row[6],  # objectid 추가
            'detected': row[7]   # detected 추가
        })
    return objects

# Flask 라우트 설정

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'rokey' and password == '1234':  
            login_user(User(username))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/get_latest_image')
@login_required
def get_latest_image():
    if web_server.latest_image is not None:
        # 이미지 리사이징 (가로, 세로 800px로 줄이기)
        resized_image = cv2.resize(web_server.latest_image, (800, 600)) 

        # 압축 품질 설정
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 50]  # 50% 품질로 압축
        _, buffer = cv2.imencode('.jpg', resized_image, encode_param)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        return jsonify({'image': f"data:image/jpeg;base64,{image_base64}"})
    else:
        return jsonify({'error': 'No image available'})

@app.route('/local_webcam')
@login_required
def local_webcam():
    cap = cv2.VideoCapture(0) 
    ret, frame = cap.read()
    cap.release()
    if ret:
        _, buffer = cv2.imencode('.jpg', frame)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        return jsonify({'image': f"data:image/jpeg;base64,{image_base64}"})
    else:
        return jsonify({'error': 'Failed to capture local webcam image'})

@app.route('/alerts', endpoint='alerts')
@login_required
def get_alerts():
    return jsonify({'alerts': web_server.alerts})

@app.route('/detected_objects_text')
@login_required
def detected_objects_text():
    objects = get_detected_objects()
    # 텍스트 형식으로 객체 정보를 변환
    object_text = "\n".join([f"ID: {obj['id']}, Class: {obj['class_name']}, Confidence: {obj['confidence']}, X: {obj['x']}, Y: {obj['y']}, Timestamp: {obj['timestamp']}, Detected: {obj['detected']}" for obj in objects])
    return jsonify({'detected_objects_text': object_text})

    
@app.route('/search_crime', methods=['GET'])
@login_required
def search_crime():
    query = request.args.get('query', '')
    conn = sqlite3.connect('/home/hyuna/지능_2/detections.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM detections WHERE class_name LIKE ?", ('%' + query + '%',))
    rows = cursor.fetchall()
    conn.close()
    objects = []
    for row in rows:
        objects.append({
            'id': row[0],
            'class_name': row[1],
            'confidence': row[2],
            'x': row[3],
            'y': row[4],
            'timestamp': row[5]
        })
    return jsonify({'results': objects})

@app.route('/amr_state')
@login_required
def amr_state():
    return jsonify({'amr_state': web_server.amr_state})

# RViz2 이미지 업로드 
@app.route('/upload_rviz_image', methods=['POST'])
@login_required
def upload_rviz_image():
    with open('static/rviz_view.jpg', 'wb') as f:
        f.write(request.data)
    return 'RViz image received', 200

@app.route('/get_rviz_image')
@login_required
def get_rviz_image():
    return send_file('static/rviz_view.jpg', mimetype='image/jpeg')

@app.route('/upload_turtlebot_image', methods=['POST'])
def upload_turtlebot_image():
    # 이미지 저장 경로 
    image_path = 'static/latest_turtlebot_image.jpg'
    abs_image_path = os.path.join(os.getcwd(), image_path)

    # 디렉토리 생성 (디렉토리가 없는 경우에만 생성)
    os.makedirs(os.path.dirname(abs_image_path), exist_ok=True)

    # 이미지 저장
    with open(abs_image_path, 'wb') as f:
        f.write(request.data)
    print(f"TurtleBot image received and saved at: {abs_image_path}")
    return 'TurtleBot image received', 200

@app.route('/get_turtlebot_image')
def get_turtlebot_image():
    image_path = 'static/latest_turtlebot_image.jpg'
    abs_image_path = os.path.join(os.getcwd(), image_path)

    if os.path.exists(abs_image_path):
        return send_file(abs_image_path, mimetype='image/jpeg')
    else:
        print("Error: TurtleBot image not found.")
        return "Error: TurtleBot image not found.", 404

def run_flask():
    app.run(host='0.0.0.0', port=8000, debug=True, use_reloader=False)

def main(args=None):
    rclpy.init(args=args)
    global web_server
    web_server = WebServer()

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    try:
        rclpy.spin(web_server)
    except KeyboardInterrupt:
        pass
    finally:
        web_server.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
