let devices = []
let selectedDevice = null
let isDragging = false

// 初期化時にサーバーから既存デバイスを取得して表示
function initMap() {
    const mapContainer = document.getElementById('mapContainer')

    // サーバーから既に設定されたデバイスを取得
    fetch('/get_receiver_positions')
        .then((response) => response.json())
        .then((data) => {
            devices = data.receivers
            devices.forEach((device) => {
                addDeviceMarker(device)
            })
        })
        .catch((error) => console.error('Error fetching devices:', error))

    mapContainer.addEventListener('click', function (event) {
        const { x, y } = getRelativeCoordinates(event, mapContainer)

        const deviceId = prompt('Enter Receiver Device ID:')
        if (deviceId) {
            const newDevice = { device_id: deviceId, position: { x, y } }
            devices.push(newDevice)
            addDeviceMarker(newDevice)
        }
    })
}

// デバイスマーカーを作成・表示
function addDeviceMarker(device) {
    const mapContainer = document.getElementById('mapContainer')
    const marker = document.createElement('div')
    marker.classList.add('marker')
    updateMarkerPosition(marker, device.position, mapContainer)
    marker.innerText = device.device_id
    marker.dataset.deviceId = device.device_id

    // ドラッグイベントの設定
    marker.addEventListener('mousedown', function (event) {
        selectedDevice = device
        isDragging = true
    })

    // ダブルクリックでデバイス編集
    marker.addEventListener('dblclick', function (event) {
        const newDeviceId = prompt('Edit Device ID:', device.device_id)
        if (newDeviceId) {
            device.device_id = newDeviceId
            marker.innerText = newDeviceId
        }
    })

    mapContainer.appendChild(marker)
}

// マーカーの位置を更新（座標は画像に対する割合）
function updateMarkerPosition(marker, position, mapContainer) {
    const containerWidth = mapContainer.offsetWidth
    const containerHeight = mapContainer.offsetHeight
    const left = position.x * containerWidth
    const top = position.y * containerHeight
    marker.style.left = `${left}px`
    marker.style.top = `${top}px`
}

// マウス移動時のイベント
document.addEventListener('mousemove', function (event) {
    if (isDragging && selectedDevice) {
        const mapContainer = document.getElementById('mapContainer')
        const { x, y } = getRelativeCoordinates(event, mapContainer)
        selectedDevice.position.x = x
        selectedDevice.position.y = y
        const marker = document.querySelector(`.marker[data-device-id="${selectedDevice.device_id}"]`)
        updateMarkerPosition(marker, selectedDevice.position, mapContainer)
    }
})

// マウスボタンが離れたときのイベント
document.addEventListener('mouseup', function () {
    isDragging = false
    selectedDevice = null
})

// マウス座標を画像に対する割合で取得
function getRelativeCoordinates(event, container) {
    const rect = container.getBoundingClientRect()
    const x = (event.clientX - rect.left) / container.offsetWidth
    const y = (event.clientY - rect.top) / container.offsetHeight
    return { x: Math.min(1, Math.max(0, x)), y: Math.min(1, Math.max(0, y)) }
}

// 保存ボタン押下時にデバイスの位置をサーバーに送信
function saveDevicePositions() {
    fetch('/save_receiver_positions', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ devices })
    })
        .then((response) => response.json())
        .then((data) => alert('Devices saved successfully'))
        .catch((error) => console.error('Error saving devices:', error))
}

window.onload = initMap