document.addEventListener('DOMContentLoaded', function() {
    const latestImageElement = document.getElementById('latest-image');
    const systemStatusElement = document.getElementById('system-status');

    function updateLatestImage() {
        fetch('/get_latest_image')
            .then(response => response.json())
            .then(data => {
                if (data.image) {
                    latestImageElement.src = data.image;
                } else {
                    console.log('No image available');
                }
            })
            .catch(error => console.error('Error:', error));
    }

    function updateSystemStatus() {
        fetch('/get_system_status')
            .then(response => response.json())
            .then(data => {
                systemStatusElement.textContent = data.status;
            })
            .catch(error => console.error('Error:', error));
    }

    // 주기적으로 이미지와 시스템 상태 업데이트
    setInterval(updateLatestImage, 1000);
    setInterval(updateSystemStatus, 1000);
});
