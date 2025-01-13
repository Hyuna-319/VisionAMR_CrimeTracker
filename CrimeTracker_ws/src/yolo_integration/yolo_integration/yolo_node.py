import rclpy

from rclpy.node import Node

import cv2

import numpy as np

from ultralytics import YOLO

from sensor_msgs.msg import Image

from std_msgs.msg import String

from geometry_msgs.msg import Point

from cv_bridge import CvBridge

import requests

from datetime import datetime

import sqlite3
from geometry_msgs.msg import Twist
from geometry_msgs.msg import Pose

class YoloNode(Node):

    def __init__(self):

        super().__init__('yolo_node')

        

        

        self.alert_url = "http://192.168.10.42:8000/alert"

        

        # YOLO 모델 로드 (crime/dummy 전용 모델 및 COCO 기반 모델)

        self.model = YOLO('/home/hyuna/지능_2/src/yolo_integration/yolo_integration/best.pt') # crime 및 dummy만 탐지

        self.coco_model = YOLO('yolov8n.pt')  # COCO 데이터셋 기반 일반 객체 탐지 모델

        

        

        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():

            self.get_logger().error("웹캠 연결 실패")

            return

        

        # 기준선 설정

        self.line_x = 380

        self.line_y_start = 65

        self.line_y_end = 295



        # 객체 위치 기록용 변수

        self.previous_positions = {}

        self.detected_objects = {}

        self.detected_object_db = {}

        self.id_counter = 1  # 객체 ID 카운터



        

        self.publisher_ = self.create_publisher(Image, 'detected_image', 10)

        self.status_publisher_ = self.create_publisher(String, 'system_status', 10)

        self.object_position_publisher = self.create_publisher(Point, 'detected_object', 10)
        self.start_pose_publisher = self.create_publisher(Pose, 'turtlebot3/start_pose', 10)  # 출발 위치 퍼블리셔
        self.bridge = CvBridge()



        

        self.initialize_database()
    
        self.timer = self.create_timer(0.1, self.timer_callback)
    


    def initialize_database(self):

        
        conn = sqlite3.connect('/home/user/ros2_ws/detections.db')

        cursor = conn.cursor()

        

        # 테이블 생성

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT,
            objectid TEXT,
            confidence REAL,
            x REAL,
            y REAL,
            timestamp TEXT,
            detected INTEGER
        )
        ''')

        

        conn.commit()

        conn.close()

    # 출발 명령
    def publish_start_signal(self):
        msg = String()
        msg.data = 'start'  
        self.publisher.publish(msg)
        self.get_logger().info(f"Published start signal: {msg.data}")

    def save_detection_to_db(self, class_name, objectid, confidence, x, y, timestamp, detected):
        try:
            conn = sqlite3.connect('/home/user/ros2_ws/detections.db')
            cursor = conn.cursor()
            cursor.execute('''
            INSERT INTO detections (class_name, objectid, confidence, x, y, timestamp, detected)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (str(class_name), str(objectid), float(confidence), float(x), float(y), str(timestamp), int(detected)))
            conn.commit()
        except sqlite3.Error as e:
            self.get_logger().error(f"Database error: {e}")
        except Exception as e:
            self.get_logger().error(f"Unexpected error: {e}")
        finally:
            if conn:
                conn.close()



    def timer_callback(self):

        ret, frame = self.cap.read()

        if not ret:

            self.get_logger().error("카메라에서 이미지를 가져올 수 없습니다.")

            return



        # YOLO 객체 탐지 (crime/dummy 모델과 COCO 모델)

        results_crime = self.model(frame)

        results_coco = self.coco_model(frame)

        detected_count = 0




        detection_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")



        # crime/dummy 모델에서 감지된 객체 처리

        for result in results_crime:

            boxes = result.boxes

            for box in boxes:

                x_min, y_min, x_max, y_max = map(int, box.xyxy[0])

                class_name = self.model.names[int(box.cls[0])]

                confidence = box.conf[0]



                # 객체의 중앙 위치 계산

                center_x = (x_min + x_max) / 2

                center_y = (y_min + y_max) / 2



                # 객체 식별을 위한 ID 부여

                object_id = self.get_object_id(class_name, (x_min, y_min, x_max, y_max))

                if object_id not in self.detected_objects:

                    self.detected_objects[object_id] = None  # 객체가 감지된 것으로 표시

                    self.detected_object_db[object_id] = 0



                # 기준선을 넘는지 확인하고 crime 객체만 AMR에 전송

                if self.is_crossing_line(self.previous_positions.get(object_id), (x_min, y_min, x_max, y_max)):

                    if self.detected_objects[object_id] is None:

                        self.detected_objects[object_id] = self.id_counter

                        self.id_counter += 1

                        self.detected_object_db[object_id] = 1

                    

                    if not self.detected_objects[object_id]:  # 처음으로 선을 넘을 때만 저장

                        self.detected_objects[object_id] = True  # 객체가 감지된 것으로 표시

                    object_id_num = self.detected_objects[object_id]



                    if class_name == "crime":

                        # AMR에 crime 객체 좌표 전송

                        detected_object_position = Point()

                        detected_object_position.x = center_x

                        detected_object_position.y = center_y

                        self.object_position_publisher.publish(detected_object_position)

                        self.publisher = self.create_publisher(String, 'start_signal', 10)

                        # 상태 메시지 퍼블리시

                        if(self.id_counter - 1) <= self.detected_objects[object_id]:

                            status_message = f"{object_id} : {detection_time}"

                            self.publish_status(status_message)

                            self.get_logger().info(status_message)


                        # 화면에 Detect 표시

                        cv2.putText(frame, "DETECT", (x_min, y_min - 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
                        
                    

                     

                    self.save_detection_to_db(class_name, object_id, confidence, center_x, center_y, detection_time, self.detected_object_db[object_id])



                    # Flask 서버로 알림 전송

                    alert_data = {

                        'timestamp': detection_time,

                        'detected_count': detected_count + 1

                    }

                    try:

                        response = requests.post(self.alert_url, json=alert_data)

                        if response.status_code == 200:

                            self.get_logger().info(f"Alert sent: Detected objects = {alert_data['detected_count']} at {alert_data['timestamp']}")

                    except requests.exceptions.RequestException as e:

                        self.get_logger().error(f"Failed to send alert: {e}")



                    # 화면에 ID 표시

                    cv2.putText(frame, f"ID: {object_id_num}", (x_min, y_min + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 255), 2)

                    self.get_logger().info(f"ID: {object_id_num} - 탐지됨: '{class_name}' 객체가 기준선을 넘었습니다!")

                

                # 객체 위치 업데이트

                self.previous_positions[object_id] = (x_min, y_min, x_max, y_max)

                detected_count += 1



                # 탐지 결과 이미지에 텍스트 및 박스 표시

                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                cv2.putText(frame, f"{class_name} {confidence:.2f}", (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)



        # COCO 모델에서 추가로 감지된 객체 처리

        for result in results_coco:

            boxes = result.boxes

            for box in boxes:

                x_min, y_min, x_max, y_max = map(int, box.xyxy[0])

                class_name = self.coco_model.names[int(box.cls[0])]

                confidence = box.conf[0]



                # COCO 모델에서는 crime/dummy를 제외한 객체만 처리

                if class_name in ['crime', 'dummy']:

                    continue



                object_id = self.get_object_id(class_name, (x_min, y_min, x_max, y_max))

                if object_id not in self.detected_objects:

                    self.detected_objects[object_id] = None



                # 기준선을 넘었는지 확인하고 ID 부여

                if self.is_crossing_line(self.previous_positions.get(object_id), (x_min, y_min, x_max, y_max)):

                    if self.detected_objects[object_id] is None:

                        self.detected_objects[object_id] = self.id_counter

                        self.id_counter += 1

                    

                    object_id_num = self.detected_objects[object_id]



                    # 화면에 ID 표시

                    cv2.putText(frame, f"ID: {object_id_num}", (x_min, y_min + 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 255), 2)

                    self.get_logger().info(f"ID: {object_id_num} - 탐지됨: '{class_name}' 객체가 기준선을 넘었습니다!")



                # 위치 업데이트

                self.previous_positions[object_id] = (x_min, y_min, x_max, y_max)

                detected_count += 1



                # 탐지 결과 이미지 표시

                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (255, 255, 0), 2)

                cv2.putText(frame, f"{class_name} {confidence:.2f}", (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)



        # 기준선 그리기

        cv2.line(frame, (self.line_x, self.line_y_start), (self.line_x, self.line_y_end), (255, 0, 0), 2)



        # 결과 이미지 

        ros_image = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")

        self.publisher_.publish(ros_image)



        

        cv2.imshow("Detection", frame)

        cv2.waitKey(1)



    def publish_status(self, message):

        status_msg = String()

        status_msg.data = message

        self.status_publisher_.publish(status_msg)



    def is_crossing_line(self, prev_bbox, current_bbox):

        if prev_bbox is None:

            return False

        prev_x_center = (prev_bbox[0] + prev_bbox[2]) // 2

        prev_y_bottom = prev_bbox[3]



        curr_x_center = (current_bbox[0] + current_bbox[2]) // 2

        curr_y_bottom = current_bbox[3]



        return prev_x_center <= self.line_x < curr_x_center and self.line_y_start <= curr_y_bottom <= self.line_y_end



    # 객체 ID를 얻기 위한 함수

    def get_object_id(self, class_name, current_bbox):

        for obj_id, prev_bbox in self.previous_positions.items():

            if obj_id.startswith(class_name) and self.is_same_object(prev_bbox, current_bbox):

                return obj_id

        return f"{class_name}-{self.id_counter}"



    # 동일한 객체인지 확인하는 함수

    def is_same_object(self, prev_bbox, current_bbox, threshold=50):

        prev_center = ((prev_bbox[0] + prev_bbox[2]) // 2, (prev_bbox[1] + prev_bbox[3]) // 2)

        curr_center = ((current_bbox[0] + current_bbox[2]) // 2, (current_bbox[1] + current_bbox[3]) // 2)

        distance = np.linalg.norm(np.array(prev_center) - np.array(curr_center))

        return distance < threshold



def main(args=None):

    rclpy.init(args=args)

    node = YoloNode()

    rclpy.spin(node)

    node.cap.release()

    cv2.destroyAllWindows()

    rclpy.shutdown()



if __name__ == '__main__':

    main()
