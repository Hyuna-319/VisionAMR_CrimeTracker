from setuptools import find_packages, setup

package_name = 'turtlebot3_move'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='hyuna',
    maintainer_email='sjajmh6612@naver.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [ 
        'turtleview = turtlebot3_move.detect_and_send:main',
        'rviz_capture = turtlebot3_move.rviz_capture_and_send:main'
        ],
    },
)
