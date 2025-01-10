import rclpy
from rclpy.node import Node
import cv2
from ultralytics import YOLO
from sensor_msgs.msg import Image, Range
from std_msgs.msg import String
from geometry_msgs.msg import Twist, PoseStamped
from sensor_msgs.msg import Range
from cv_bridge import CvBridge
import requests
from datetime import datetime
import time

class YoloAMRNode(Node):
    def __init__(self):
        super().__init__('yolo_amr_node')

        
        self.model = YOLO('/home/rokey9/turtle_ws/src/best.pt')
       

        # 웹캠 연결
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            self.get_logger().error("웹캠 연결 실패")
            return

        # Flask 서버로 이미지 전송 
        self.flask_url = "http://192.168.10.42:8000/upload_turtlebot_image"

        
        self.bridge = CvBridge()

        # 이동 명령 
        self.cmd_vel_publisher = self.create_publisher(Twist, '/cmd_vel', 10)
        # goal_pose 
        self.goal_publisher = self.create_publisher(PoseStamped, '/move_base_simple/goal', 10)

        self.create_subscription(String, 'start_signal', self.start_signal_callback, 10)
        
        self.return_check_url = "http://192.168.10.42:8000/check_return_signal"  # 복귀 신호를 확인할 URL
        self.timer = self.create_timer(0.2, self.timer_callback)
        self.target_area_threshold = 0.75  # 화면의 75% 크기를 기준으로 설정
       

        # 초기 위치와 목표 위치 설정
        self.initial_pose = PoseStamped()
        self.initial_pose.header.frame_id = 'map'
        self.initial_pose.pose.position.x = 0.06882742047309875
        self.initial_pose.pose.position.y = 0.015280992724001408
        self.initial_pose.pose.orientation.w = 0.9998471004702795

        """self.goal_pose = PoseStamped() # 테스트용
        self.goal_pose.header.frame_id = "map"
        self.goal_pose.pose.position.x = 1.5000029802322388  # 목표 x 좌표
        self.goal_pose.pose.position.y = -0.771869421005249  # 목표 y 좌표
        self.goal_pose.pose.orientation.w = 0.7216740076140788"""

        # 상태 
        self.crime_detected = False
        self.is_obstacle_detected = False
        self.stopped_due_to_crime = False  # crime 때문에 멈췄는지 추적

    def start_signal_callback(self, msg):
        if msg.data == "start":
            self.get_logger().info("목표 위치로 이동합니다.")
            self.start_navigation()
            self.crime_detected = True

    def timer_callback(self):
        
        ret, frame = self.cap.read()
        if not ret:
            self.get_logger().error("카메라에서 이미지를 가져올 수 없습니다.")
            return

        # YOLO 모델로 객체 감지 수행
        results = self.model(frame, imgsz=640)
        annotated_frame = results[0].plot()

        # 탐지된 이미지를 JPEG 형식으로 Flask 서버에 전송
        _, img_encoded = cv2.imencode('.jpg', annotated_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 30])
        try:
            response = requests.post(self.flask_url, data=img_encoded.tobytes(), headers={'Content-Type': 'image/jpeg'})
            if response.status_code == 200:
                self.get_logger().info("Image uploaded successfully.")
            else:
                self.get_logger().warn(f"Failed to upload image. Status code: {response.status_code}")
        except Exception as e:
            self.get_logger().error(f"Error sending image: {e}")

        # crime 객체에 대한 위치 및 크기 계산
        self.crime_detected = False
        for result in results:
            boxes = result.boxes
            for box in boxes:
                x_min, y_min, x_max, y_max = map(int, box.xyxy[0])
                class_name = self.model.names[int(box.cls[0])]
                area = (x_max - x_min) * (y_max - y_min) / (frame.shape[0] * frame.shape[1])

                if class_name == "crime":
                    self.crime_detected = True
                    # crime 객체가 75% 이상 크기일 경우 멈추고 추적 중지
                    if area > self.target_area_threshold:
                        self.stop_movement()
                        self.stopped_due_to_crime = True
                    else:
                        # crime 객체가 75% 이하로 작아졌으면 추적 재개
                        if self.stopped_due_to_crime:
                            self.get_logger().info("Crime has moved away, resuming tracking.")
                            self.stopped_due_to_crime = False
                        # crime 객체의 중심 x좌표 기준으로 TurtleBot3 이동
                        crime_center_x = (x_min + x_max) / 2
                        frame_center_x = frame.shape[1] / 2
                        self.align_and_approach_crime(crime_center_x, frame_center_x)

        # crime 객체가 없으면 이동을 멈추고 대기
        if not self.crime_detected and not self.is_obstacle_detected:
            self.stop_movement()

        # 복귀 신호 확인
        self.check_return_signal()

        # 디버깅을 위해 탐지된 프레임을 화면에 표시
        cv2.imshow("Annotated Frame", annotated_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.destroy_node()

    def align_and_approach_crime(self, crime_center_x, frame_center_x):
        twist = Twist()
        # 화면 중심과 crime 중심의 차이를 기준으로 회전 및 전진 명령 설정
        if abs(crime_center_x - frame_center_x) > 20:
            # crime 중심이 화면 중심에서 벗어나면 회전
            twist.angular.z = float(0.1) if crime_center_x < frame_center_x else float(-0.1)
        else:
            twist.angular.z = float(0)  # 중심에 맞춘 경우 회전 중지
            twist.linear.x = 0.1  # 앞으로 전진

        self.get_logger().info(f"Publishing twist: linear.x = {twist.linear.x}, angular.z = {twist.angular.z}")
        self.cmd_vel_publisher.publish(twist)

    def stop_movement(self):
        twist = Twist()
        twist.linear.x = 0.0
        twist.angular.z = float(0)
        self.cmd_vel_publisher.publish(twist)
        self.get_logger().info("Crime detected close by. Stopping movement.")

    def avoid_obstacle(self):
        # 장애물이 감지되었을 때 회피 동작
        twist = Twist()
        twist.linear.x = 0  # 전진 중지
        twist.angular.z = float(0.5)  # 오른쪽으로 회전
        self.cmd_vel_publisher.publish(twist)
        self.get_logger().info("Obstacle detected. Avoiding obstacle.")

    def check_return_signal(self):
        try:
            response = requests.get(self.return_check_url)
            if response.status_code == 200:
                return_signal = response.json().get("return_signal", False)
                if return_signal:
                    self.return_to_initial_pose()
        except Exception as e:
            self.get_logger().error(f"Error checking return signal: {e}")

    def return_to_initial_pose(self):
        # 초기 위치로 목표 위치 설정
        self.initial_pose.header.stamp = self.get_clock().now().to_msg()
        self.goal_publisher.publish(self.initial_pose)
        self.get_logger().info("초기 위치로 복귀합니다.")

    def destroy_node(self):
        super().destroy_node()
        self.cap.release()
        cv2.destroyAllWindows()

def main(args=None):
    rclpy.init(args=args)
    node = YoloAMRNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

