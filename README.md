🚔 AI 비전 & 범죄 차량 추적 시스템 구축
=============
YOLOv8, Jetson Nano 기반 카메라 인식·물체 추적 기능을 통합한 감시 시스템 구축

[프로젝트 기록](https://velog.io/@cherry0319/AI-%EB%B9%84%EC%A0%84-%EB%B2%94%EC%A3%84-%EC%B0%A8%EB%9F%89-%EC%B6%94%EC%A0%81-%EC%8B%9C%EC%8A%A4%ED%85%9C-%EA%B5%AC%EC%B6%95-I)

<br>

인원 및 기간
-------------
* 3명 : [김현아](https://github.com/Hyuna-319), [장석환](https://github.com/JSH0101), [홍유진](https://github.com/dbwls99706)
* 2024.11.05 ~ 2024.11.11 (7일)

<br>

사용 기술
-------------
* Language : Python3
* OS : Linux Ubuntu 22.04 jammy
* Hardware: Turtlebot3 burger
* Skills : ROS2 Humble, Gazebo11, Rviz2, Nav2, Turtlebo3 Packages, OpenCV, LabelImg, YOLOv8, Flask, SQLite3

<br>

특징
-------------
* Security Zone
  - CCTV(웹 카메라)를 활용해 보안 구역 내 침입 객체를 상시 감시
  - 침입 감지시 system monitor에 즉각 알림 전송
  - 침입 객체를 분석하여 범죄 차량(crime)과 일반 객체를 구분하여 인식

<br>

* AMR Auto Traking
  - 범죄 차량(crime)이 탐지되면 자동으로 추적
  - 범죄 차량(crime)과 장애물(dummy)을 구분하여 인식
  
<br>

* System Monitor
  - 관리자 전용 로그인 화면을 구현하여 보안 강화
  - 관리자가 상황을 파악할 수 있도록 CCTV 화면과 AMR 카메라 화면 표시
  - 알림창을 통해 감지된 객체 정보와 검거 완료 여부를 제공
    
<br>

* DataBase
  - 감지된 객체 정보를 데이터베이스에 저장하여 데이터 추적 및 분석 가능

<br>

보완 사항
-------------
* AMR과 통신을 통해 목표 위치 설정 및 이동 구현
* Sytem Monitor AMR의 실시간 화면, 지도 정보 전송
* System Monitor로 범인 검거 메시지 송신
* AMR이 System Monitor로부터 초기 위치 복귀 명령 수신 후 자동으로 복귀

<br>
<br>

프로젝트 결과
-------------

<br>

**결과 이미지**

![image (2)](https://github.com/user-attachments/assets/5285d16b-5a2c-4db0-b8fe-2720b1e2a417)



<br>

 

**결과 동영상**

![결과 동영상)](https://github.com/user-attachments/assets/386dc8e8-8e45-466c-bb7c-fa0038fd3a2c)
