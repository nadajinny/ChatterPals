let floatingBtn = null;
let sidebarIframe = null;

/**
 * 플로팅 버튼을 생성하고, 클릭 및 드래그 이벤트를 설정합니다.
 */
function createFloatingButton() {
    if (document.getElementById('chatterpals-floating-btn')) return;

    floatingBtn = document.createElement('div');
    floatingBtn.id = 'chatterpals-floating-btn';
    document.body.appendChild(floatingBtn);

    let isDragging = false;
    let dragStartX, dragStartY;
    let offsetX, offsetY;

    // 드래그 시작 이벤트
    floatingBtn.addEventListener('mousedown', (e) => {
        // 드래그 관련 변수 초기화
        isDragging = false;
        dragStartX = e.clientX;
        dragStartY = e.clientY;
        offsetX = e.clientX - floatingBtn.getBoundingClientRect().left;
        offsetY = e.clientY - floatingBtn.getBoundingClientRect().top;
        
        // 드래그 동작을 감지하기 위한 이벤트 리스너를 문서 전체에 추가
        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    });

    // 마우스를 움직일 때의 처리
    function onMouseMove(e) {
        // 시작점과 현재 위치의 거리를 계산
        const movedDistance = Math.sqrt(Math.pow(e.clientX - dragStartX, 2) + Math.pow(e.clientY - dragStartY, 2));

        // 5픽셀 이상 움직였을 경우에만 드래그로 간주
        if (movedDistance > 5) {
            isDragging = true;
            floatingBtn.style.cursor = 'grabbing';
            floatingBtn.style.transition = 'none';

            let newX = e.clientX - offsetX;
            let newY = e.clientY - offsetY;

            // 화면 밖으로 나가지 않도록 좌표 제한
            newX = Math.max(0, Math.min(newX, window.innerWidth - floatingBtn.offsetWidth));
            newY = Math.max(0, Math.min(newY, window.innerHeight - floatingBtn.offsetHeight));

            floatingBtn.style.left = `${newX}px`;
            floatingBtn.style.top = `${newY}px`;
            floatingBtn.style.right = 'auto';
            floatingBtn.style.bottom = 'auto';
        }
    }

    // 마우스 버튼을 놓았을 때의 처리
    function onMouseUp(e) {
        // 드래그가 아니었다면 '클릭'으로 간주하고 사이드바 토글
        if (!isDragging) {
            console.log("ChatterPals: Click detected. Toggling sidebar.");
            toggleSidebar();
        } else {
            console.log("ChatterPals: Drag ended.");
        }

        // 이벤트 리스너 정리
        floatingBtn.style.cursor = 'grab';
        floatingBtn.style.transition = 'transform 0.2s ease-in-out, box-shadow 0.2s ease';
        document.removeEventListener('mousemove', onMouseMove);
        document.removeEventListener('mouseup', onMouseUp);
    }
}

/**
 * 사이드바를 열거나 닫는 토글 함수
 */
function toggleSidebar() {
    if (sidebarIframe) { // 사이드바가 열려있으면 닫기
        sidebarIframe.classList.remove('visible');
        if (floatingBtn) floatingBtn.style.zIndex = '99999990';
        setTimeout(() => {
            if (sidebarIframe) sidebarIframe.remove();
            sidebarIframe = null;
        }, 300);
    } else { // 사이드바가 닫혀있으면 열기
        sidebarIframe = document.createElement('iframe');
        sidebarIframe.id = 'chatterpals-sidebar-iframe';
        sidebarIframe.src = chrome.runtime.getURL('popup.html?context=sidebar');
        document.body.appendChild(sidebarIframe);
        
        if (floatingBtn) floatingBtn.style.zIndex = '99999999';
        
        setTimeout(() => {
            if (sidebarIframe) sidebarIframe.classList.add('visible');
        }, 50);
    }
}

// 스크립트 초기화: 최상위 페이지에서만 버튼 생성
if (window.self === window.top) {
    createFloatingButton();
}

