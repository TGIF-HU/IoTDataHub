// ヒストグラム用の色の定義
const receiverColors = ['rgba(75, 192, 192, 0.6)', 'rgba(192, 75, 192, 0.6)', 'rgba(192, 192, 75, 0.6)', 'rgba(75, 192, 75, 0.6)']

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


window.onload = function () {
    initializeHistogram() // ヒストグラムを初期化
    setInterval(fetchValidDevices, 500) // 5秒ごとに有効デバイス数を更新
    setInterval(fetchDeviceRSSI, 500) // 5秒ごとにRSSIデータを更新
}