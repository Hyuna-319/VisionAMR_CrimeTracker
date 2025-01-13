from setuptools import setup, find_packages

package_name = 'yolo_integration'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Launch files
        ('share/' + package_name + '/launch', ['launch/yolo_launch.py']),
        # Templates and static files
        ('share/' + package_name + '/templates', [
            'yolo_integration/templates/alerts.html',
            'yolo_integration/templates/dashboard.html',
            'yolo_integration/templates/login.html',
            'yolo_integration/templates/popup.html',
        ]),
        ('share/' + package_name + '/static/css', [
            'yolo_integration/static/css/style.css',
        ]),
        ('share/' + package_name + '/static/js', [
            'yolo_integration/static/js/main.js',
        ]),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='hyuna',
    maintainer_email='sjajmh6612@naver.com',
    description='YOLOv8 integration with ROS 2 and Flask web server',
    license='Apache License 2.0',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'yolo_node = yolo_integration.yolo_node:main',
            'web_server = yolo_integration.web_server:main',
            'pose = yolo_integration.robot_pose_subscriber:main',
            

        ],
    },

)
