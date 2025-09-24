// 이 페이지는 로드되자마자 마이크 권한을 요청하고, 결과를 background에 알린 후 스스로 닫힙니다.
(async function requestPermission() {
  try {
    // 마이크 권한 요청창을 즉시 띄웁니다.
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // 권한을 얻었으므로, 실제 녹음은 offscreen에서 할 수 있도록 스트림은 바로 닫습니다.
    stream.getTracks().forEach(track => track.stop());
    
    // background에 성공 메시지를 보냅니다.
    chrome.runtime.sendMessage({ action: 'permissionResult', success: true });

  } catch (error) {
    // 사용자가 '거부'를 누르거나 오류가 발생했을 때
    console.error("마이크 권한 요청 실패:", error);
    chrome.runtime.sendMessage({ action: 'permissionResult', success: false, error: error.message });
  } finally {
    // 성공하든 실패하든, 이 창은 역할을 다했으므로 닫습니다.
    window.close();
  }
})();
