// デバイスの位置情報を取得
// function fetchDevicePositions() {
//   fetch('/get_device_positions_and_receiver_positions')
//     .then((response) => response.json())
//     .then((data) => {
//       receiverPositions = data.receivers // 受信デバイスの位置を格納
//       updateDeviceMap(data) // 地図上にデバイスを表示
//     })
//     .catch((error) => console.error('Error fetching device positions:', error))
// }


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
  // fetchDevicePositions() // デバイス位置取得
  // setInterval(fetchDevicePositions, 500) // 5秒ごとに位置データを更新
}