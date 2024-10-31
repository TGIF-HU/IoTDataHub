// スキャンされたデバイス情報を取得
function fetchScannedDevices() {
    fetch('/api/scanned_devices')
        .then((response) => response.json())
        .then((data) => {
            const deviceList = document.getElementById('deviceList');
            deviceList.innerHTML = ''; // リストをクリア

            data.forEach((device) => {
                const listItem = document.createElement('li');
                const deviceName = device.name || '(no name)';
                const manufactureId = device.manufacture_id;
                const timestamp = new Date(device.timestamp).toLocaleString();

                listItem.innerHTML = `
            <strong>Device ID:</strong> ${device.device_id}<br>
            <strong>MAC Address:</strong> ${device.mac_address}<br>
            <strong>Manufacture ID:</strong> [${manufactureId}]<br>
            <strong>Name:</strong> ${deviceName}<br>
            <strong>Timestamp:</strong> ${timestamp}<br>
            <strong>RSSI:</strong> ${device.rssi} dBm<br>
        `;

                deviceList.appendChild(listItem);
            });
        })
        .catch((error) => {
            console.error('Error fetching devices:', error);
        });
}

window.onload = function () {
    setInterval(fetchScannedDevices, 500); // 5秒ごとにスキャンされたデバイス情報を更新
}