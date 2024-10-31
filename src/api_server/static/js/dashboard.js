let receiverPositions = [] // 受信デバイスの位置を格納

// ヒストグラム用の色の定義
const receiverColors = ['rgba(75, 192, 192, 0.6)', 'rgba(192, 75, 192, 0.6)', 'rgba(192, 192, 75, 0.6)', 'rgba(75, 192, 75, 0.6)']

// 有効デバイス数を取得
function fetchValidDevices() {
  fetch('/api/valid_devices')
    .then((response) => response.json())
    .then((data) => {
      document.getElementById('deviceCount').innerText = data.valid_device_count
      const now = new Date()
      const formattedTime = now.toLocaleString()
      document.getElementById('lastUpdated').innerText = formattedTime
    })
    .catch((error) => console.error('Error fetching valid device count:', error))
}

// デバイスの位置情報を取得
function fetchDevicePositions() {
  fetch('/get_device_positions_and_receiver_positions')
    .then((response) => response.json())
    .then((data) => {
      receiverPositions = data.receivers // 受信デバイスの位置を格納
      updateDeviceMap(data) // 地図上にデバイスを表示
    })
    .catch((error) => console.error('Error fetching device positions:', error))
}

// RSSIデータを取得してヒストグラムを更新
function fetchDeviceRSSI() {
  fetch('/api/rssi')
    .then((response) => response.json())
    .then((data) => {
      deviceData = data // RSSIデータを格納
      updateHistogram() // ヒストグラムを更新
    })
    .catch((error) => console.error('Error fetching device RSSI:', error))
}

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

function initializeHistogram() {
  const ctx = document.getElementById('rssiChart').getContext('2d')
  rssiChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: [], // 初期化時には空のラベル
      datasets: []
    },
    options: {
      animation: false,
      scales: {
        x: {
          title: {
            display: true,
            text: 'RSSI (dBm)'
          }
        },
        y: {
          title: {
            display: true,
            text: 'デバイス数'
          },
          beginAtZero: true,
          ticks: {
            stepSize: 1 // 自然数単位で表示
          }
        }
      }
    }
  })
}

function updateHistogram() {
  // RSSIの範囲を10刻みで指定
  const rssiRange = Array.from({ length: 11 }, (_, i) => -100 + i * 10)
  const receiverCounts = new Array(rssiRange.length).fill(0) // RSSIごとのカウント

  // 各送信デバイスのRSSIを確認して範囲ごとにカウント
  Object.keys(deviceData).forEach((receiverId) => {
    const rssiArray = deviceData[receiverId] // 各デバイスのRSSIデータ配列
    rssiArray.forEach((rssi) => {
      for (let i = 0; i < rssiRange.length; i++) {
        if (rssi < rssiRange[i]) {
          receiverCounts[i] += 1
          break
        }
      }
    })
  })

  // ヒストグラムのデータセットを作成
  const datasets = [{
    label: 'Device RSSI Distribution',
    data: receiverCounts,
    backgroundColor: 'rgba(75, 192, 192, 0.2)',
    borderColor: 'rgba(75, 192, 192, 1)',
    borderWidth: 1
  }]

  // ヒストグラムのデータを更新
  rssiChart.data.labels = rssiRange.map((rssi) => `${rssi}dBm〜`)
  rssiChart.data.datasets = datasets
  rssiChart.update() // チャートを再描画
}

function updateDeviceMap(data) {
  const ctx = document.getElementById('mapCanvas').getContext('2d')
  const mapContainer = document.getElementById('mapContainer')
  const mapWidth = mapContainer.offsetWidth
  const mapHeight = mapContainer.offsetHeight

  ctx.clearRect(0, 0, mapWidth, mapHeight) // キャンバスをクリア

  // 受信デバイスの描画
  data.receivers.forEach((device) => {
    const x = device.position.x * mapWidth
    const y = device.position.y * mapHeight
    ctx.fillStyle = 'red'
    ctx.beginPath()
    ctx.arc(x, y, 10, 0, 2 * Math.PI)
    ctx.fill()
    ctx.fillText(`Receiver ${device.device_id}`, x + 10, y)
  })

  // 送信デバイスの描画
  if (data.senders) {
    data.senders.forEach((sender) => {
      if (deviceData[sender.mac_address].name) {
        const x = sender.position.x * mapWidth
        const y = sender.position.y * mapHeight
        ctx.fillStyle = 'rgba(0, 0, 128, 1)'
        ctx.beginPath()
        ctx.arc(x, y, 10, 0, 2 * Math.PI)
        ctx.fill()
        ctx.fillText(deviceData[sender.mac_address].name, x + 10, y)
      } else {
        const x = sender.position.x * mapWidth
        const y = sender.position.y * mapHeight
        ctx.fillStyle = 'rgba(0, 128, 0, 0.2)'
        ctx.beginPath()
        ctx.arc(x, y, 10, 0, 2 * Math.PI)
        ctx.fill()
      }
    })
  }
}

window.onload = function () {
  initializeHistogram() // ヒストグラムを初期化
  fetchValidDevices() // 有効デバイス数を取得
  fetchDevicePositions() // デバイス位置取得
  fetchDeviceRSSI() // RSSIデータを取得
  fetchScannedDevices() // スキャンされたデバイス情報を取得
  setInterval(fetchValidDevices, 500) // 5秒ごとに有効デバイス数を更新
  // setInterval(fetchDevicePositions, 500) // 5秒ごとに位置データを更新
  setInterval(fetchDeviceRSSI, 500) // 5秒ごとにRSSIデータを更新
  setInterval(fetchScannedDevices, 500) // 5秒ごとにスキャンされたデバイス情報を更新
}